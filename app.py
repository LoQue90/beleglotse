# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Lorenz Uhlig
"""BelegLotse 3.1.1 - ausschließlich lokale Verarbeitung."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'vendor'))
from recognition import extract, extract_fields, tesseract_path, label_list
import csv, io, json, re, hashlib, sqlite3, secrets, os, webbrowser, shutil
from datetime import datetime
from decimal import Decimal
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

LOCAL=ROOT/'lokal.json'
DATABASE=None
TOKEN=secrets.token_urlsafe(32)
SCANS={}; PLANS={}
DEFAULT={'input':'','target':'','monthly':False,'number_source':'internal','ocr':True,'tesseract':'','prefix':'VTUER','year_digits':2,'sequence_digits':3,'annual_reset':True,'filename_pattern':'{belegnummer}_{aussteller}.pdf'}
SHARED=('monthly','number_source','ocr','prefix','year_digits','sequence_digits','annual_reset','filename_pattern')

def load_json(path,default):return json.loads(path.read_text('utf-8')) if path.exists() else default.copy()
def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),'utf-8');temp.replace(path)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def cell(v):
    s=str(v).strip()
    if any(x in s for x in '\t\r\n\x00'):raise ValueError('Felder dürfen keine Tabulatoren oder Zeilenumbrüche enthalten.')
    return s

class ClosingConnection(sqlite3.Connection):
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()

def connect(path,readonly=False):
    if readonly:return sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,factory=ClosingConnection)
    return sqlite3.connect(path,timeout=10,factory=ClosingConnection)

def db():
    if DATABASE is None or not DATABASE.is_file():raise ValueError('Bitte zuerst eine Jahresdatei öffnen oder anlegen.')
    return connect(DATABASE)

def preference(c,key,default=None):
    row=c.execute('SELECT value FROM preferences WHERE name=?',(key,)).fetchone()
    return json.loads(row[0]) if row else default

def check_year_file(path):
    if not path.is_file():raise ValueError('Jahresdatei nicht vorhanden oder noch nicht lokal synchronisiert.')
    with connect(path,True) as c:
        tables={x[0] for x in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'preferences','processed','accounts','providers','counters'}.issubset(tables):raise ValueError('Keine gültige Belegimport-Jahresdatei.')
        if preference(c,'schema_version')!=3:raise ValueError('Keine unterstützte Jahresdatei. Eine Datenbank aus Version 2 kann beim Anlegen als Stammdatenvorlage ausgewählt werden.')
        year=preference(c,'bookyear')
        if not isinstance(year,int) or not 1900<=year<=2199:raise ValueError('Ungültiges Buchungsjahr.')
        if not preference(c,'file_id'):raise ValueError('Dateikennung fehlt.')
    return year

def open_year(p):
    global DATABASE
    path=Path(str(p.get('path',''))).expanduser().resolve()
    check_year_file(path)
    old=DATABASE
    try:
        DATABASE=path
        local=load_json(LOCAL,{})
        local['year_file']=str(path)
        recent=local.get('recent_files',[])
        local['recent_files']=[str(path)]+[x for x in recent if x!=str(path)][:9]
        write_json(LOCAL,local)
    except Exception:
        DATABASE=old;raise
    SCANS.clear();PLANS.clear()
    return settings()

def new_year(p):
    year=int(p['year'])
    if not 1900<=year<=2199:raise ValueError('Jahr zwischen 1900 und 2199 wählen.')
    raw=str(p.get('path','')).strip()
    if not raw:raise ValueError('Dateiname für das neue Jahr fehlt.')
    path=Path(raw).expanduser().resolve()
    if path.suffix.lower()!='.belegdb':raise ValueError('Die Jahresdatei muss auf .belegdb enden.')
    if not path.parent.is_dir():raise ValueError('Zielordner der Jahresdatei muss vorhanden sein.')
    if path.exists():raise ValueError('Diese Datei existiert bereits. Sie wird nicht überschrieben.')
    accounts=[];providers=[];prefs={k:DEFAULT[k] for k in SHARED};last=0
    template=str(p.get('template','')).strip()
    if template:
        source=Path(template).expanduser().resolve()
        if not source.is_file():raise ValueError('Vorlagendatei fehlt.')
        with connect(source,True) as c:
            tables={x[0] for x in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'accounts','providers','preferences','counters'}.issubset(tables):raise ValueError('Vorlage muss eine Jahresdatei oder Datenbank aus Version 2 sein.')
            version=preference(c,'schema_version',2)
            if version not in (2,3):raise ValueError('Version der Vorlage wird nicht unterstützt.')
            if version==3 and preference(c,'bookyear')>=year:raise ValueError('Für die Stammdatenübernahme bitte ein früheres Jahr wählen.')
            accounts=list(c.execute('SELECT number,description FROM accounts'))
            providers=list(c.execute('SELECT name,rule FROM providers'))
            for key in SHARED:
                value=preference(c,key)
                if value is not None:prefs[key]=value
            if version==2:prefs['monthly']=False
            if not prefs['annual_reset']:
                last=c.execute('SELECT COALESCE(MAX(last),0) FROM counters').fetchone()[0]
    temporary=path.parent/('.belegimport-'+secrets.token_hex(8)+'.tmp')
    created=False
    try:
        with connect(temporary) as c:
            c.executescript("""
            CREATE TABLE processed(hash TEXT PRIMARY KEY,invoice_key TEXT UNIQUE,destination TEXT,export TEXT,source TEXT,created TEXT,metadata TEXT);
            CREATE TABLE accounts(number TEXT PRIMARY KEY,description TEXT NOT NULL);
            CREATE TABLE providers(name TEXT PRIMARY KEY,rule TEXT NOT NULL);
            CREATE TABLE counters(year INTEGER PRIMARY KEY,last INTEGER NOT NULL);
            CREATE TABLE preferences(name TEXT PRIMARY KEY,value TEXT);
            """)
            c.executemany('INSERT INTO accounts VALUES (?,?)',accounts)
            c.executemany('INSERT INTO providers VALUES (?,?)',providers)
            prefs.update(schema_version=3,bookyear=year,file_id=secrets.token_hex(16))
            c.executemany('INSERT INTO preferences VALUES (?,?)',[(k,json.dumps(v,ensure_ascii=False)) for k,v in prefs.items()])
            if last:c.execute('INSERT INTO counters VALUES (?,?)',(year,last))
        with path.open('xb') as out:
            created=True;out.write(temporary.read_bytes());out.flush();os.fsync(out.fileno())
        check_year_file(path)
    except Exception:
        if created:path.unlink(missing_ok=True)
        raise
    finally:temporary.unlink(missing_ok=True)
    return open_year({'path':str(path)})

def settings():
    local=load_json(LOCAL,{})
    s=DEFAULT.copy()
    s.update(year_file=str(DATABASE) if DATABASE else '',bookyear=None,accounts=[],rules={},counters={},recent_files=local.get('recent_files',[]),tesseract=local.get('tesseract',''))
    s['legacy_template']=str(Path(local.get('data_dir',str(ROOT/'daten')))/'verarbeitet.sqlite')
    if DATABASE and DATABASE.is_file():
        with db() as c:
            for key in SHARED+('bookyear','file_id'):
                value=preference(c,key)
                if value is not None:s[key]=value
            s['accounts']=[dict(number=n,description=d) for n,d in c.execute('SELECT * FROM accounts ORDER BY number')]
            s['rules']={n:json.loads(r) for n,r in c.execute('SELECT * FROM providers ORDER BY name COLLATE NOCASE')}
            s['counters']={str(y):v for y,v in c.execute('SELECT * FROM counters')}
        s.update(local.get('paths',{}).get(s['file_id'],{}))
    s['ocr_available']=bool(tesseract_path(s['tesseract']))
    return s

def validate_naming(s):
    prefix=cell(s.get('prefix',DEFAULT['prefix']))
    if len(prefix)>30 or re.search(r'[<>:"/\\|?*]',prefix):raise ValueError('Ungültiges Belegnummer-Präfix.')
    if int(s.get('year_digits',2)) not in (0,2,4):raise ValueError('Jahresformat muss 0, 2 oder 4 Stellen haben.')
    if not 1<=int(s.get('sequence_digits',3))<=10:raise ValueError('Nummernstellen zwischen 1 und 10 wählen.')
    pattern=cell(s.get('filename_pattern',DEFAULT['filename_pattern']))
    import string
    allowed={'belegnummer','rechnungsnummer','aussteller','datum','jahr','jahr4'}
    try:
        for literal,field,fmt,conversion in string.Formatter().parse(pattern):
            if field is not None and (field not in allowed or fmt or conversion):raise ValueError('Unbekannter Platzhalter im Dateinamensschema.')
        if not pattern.strip():raise ValueError('Dateinamensschema fehlt.')
        if any(x in pattern for x in ('/','\\')):raise ValueError('Das Dateinamensschema darf keine Ordnerpfade enthalten.')
    except (KeyError,ValueError) as e:raise ValueError('Ungültiges Dateinamensschema: '+str(e)) from e

def save_settings(s):
    current=settings()
    if not current['year_file']:raise ValueError('Zuerst Jahresdatei öffnen.')
    if s.get('number_source','internal') not in ('internal','original'):raise ValueError('Ungültige Nummernwahl.')
    validate_naming(s)
    local=load_json(LOCAL,{})
    local.setdefault('paths',{})[current['file_id']]={k:str(s.get(k,'')) for k in ('input','target')}
    local['tesseract']=str(s.get('tesseract',''))
    with db() as c:
        for key in SHARED:c.execute('INSERT OR REPLACE INTO preferences VALUES (?,?)',(key,json.dumps(s.get(key,DEFAULT[key]))))
    write_json(LOCAL,local)
    return settings()

def save_account(p):
    number=cell(p['number']);description=cell(p['description'])
    if not number.isdigit() or not description:raise ValueError('Kontonummer und Beschreibung ausfüllen.')
    with db() as c:c.execute('INSERT OR REPLACE INTO accounts VALUES (?,?)',(number,description))
    return settings()

def save_rule(p):
    name=cell(p['name']);a=cell(p.get('account',''));bank=cell(p.get('bank',''))
    if not name or (bank and not bank.isdigit()):raise ValueError('Rechnungsstellername erforderlich; Geldkonto darf nur Ziffern enthalten.')
    aliases=p.get('aliases',[])
    if isinstance(aliases,str):aliases=[x.strip() for x in aliases.splitlines() if x.strip()]
    aliases=[cell(x) for x in aliases]
    exclude=[cell(x) for x in label_list(p.get('exclude',[]))]
    mode=p.get('match_mode','any')
    if mode not in ('any','all'):raise ValueError('Ungültige Verknüpfung der Erkennungsmerkmale.')
    labels={k:label_list(p.get('labels',{}).get(k,[])) for k in ('date','number','amount')}
    with db() as c:
        if p.get('create_only'):
            c.execute('BEGIN IMMEDIATE')
            if any(existing.casefold()==name.casefold() for (existing,) in c.execute('SELECT name FROM providers')):
                raise ValueError('Dieser Rechnungssteller existiert bereits. Bitte aus der Liste auswählen.')
        if a and not c.execute('SELECT 1 FROM accounts WHERE number=?',(a,)).fetchone():raise ValueError('Sachkonto zuerst in der Kontenliste anlegen.')
        c.execute('INSERT OR REPLACE INTO providers VALUES (?,?)',(name,json.dumps(dict(account=a,bank=bank,aliases=aliases,exclude=exclude,match_mode=mode,labels=labels),ensure_ascii=False)))
    return settings()

def scan(folder):
    path=Path(folder).expanduser().resolve()
    if not path.is_dir():raise ValueError('Eingangsordner existiert nicht.')
    SCANS.clear();PLANS.clear();s=settings();rows=[]
    with db() as c:
        for file in sorted(path.iterdir()):
            if file.suffix.lower()!='.pdf' or not file.is_file():continue
            try:h=digest(file)
            except OSError:continue
            try:r=extract(file,s['rules'],s['ocr'],s['tesseract'])
            except Exception as e:r=dict(provider='',date='',number='',amount='',currency='EUR',text='',note='PDF konnte nicht gelesen werden: '+str(e),read_notes=['PDF konnte nicht gelesen werden: '+str(e)],candidates={})
            rule=s['rules'].get(r['provider'],{})
            key=r['provider'].casefold()+'|'+r['number'].casefold() if r['number'] else None
            duplicate=bool(c.execute('SELECT 1 FROM processed WHERE hash=? OR invoice_key=?',(h,key)).fetchone())
            r.update(id=secrets.token_hex(12),filename=file.name,account=rule.get('account',''),bank=rule.get('bank',''),duplicate=duplicate)
            SCANS[r['id']]={'path':file,'hash':h,'text':r.pop('text'),'read_notes':r.pop('read_notes',[])};rows.append(r)
    return sorted(rows,key=lambda r:(r['date'] or '9999',r['filename'].casefold()))

def reprocess(p):
    source=SCANS.get(p['id'])
    if not source:raise ValueError('Bitte den Ordner erneut einlesen.')
    if digest(source['path'])!=source['hash']:raise ValueError('Quelldatei verändert. Bitte erneut einlesen.')
    name=cell(p.get('provider',''))
    if not name:raise ValueError('Bitte einen Rechnungssteller auswählen.')
    s=settings();result=extract_fields(source['text'],s['rules'],selected_provider=name)
    result['note']=' '.join(source.get('read_notes',[])+[result['note']]).strip()
    rule=s['rules'].get(name,{})
    key=name.casefold()+'|'+result['number'].casefold() if result['number'] else None
    with db() as c:
        duplicate=bool(c.execute('SELECT 1 FROM processed WHERE hash=? OR invoice_key=?',(source['hash'],key)).fetchone())
    result.update(account=rule.get('account',''),bank=rule.get('bank',''),duplicate=duplicate,reviewed=False,year_confirmed=False)
    PLANS.clear()
    return result

def safe(v):
    s=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',v).strip(' .')
    if not s:raise ValueError('Leerer Dateiname.')
    if s.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:s='_'+s
    return s

def make_plan(payload):
    s=settings()|payload['settings'];validate_naming(s);raw=s.get('target','').strip()
    if not raw:raise ValueError('Bitte Zielordner angeben.')
    target=Path(raw).expanduser().resolve()
    if target.exists() and not target.is_dir():raise ValueError('Zielpfad ist kein Ordner.')
    if not target.parent.is_dir():raise ValueError('Übergeordneter Zielordner muss vorhanden sein.')
    rows=payload['rows']
    if not rows:raise ValueError('Bitte mindestens eine Rechnung auswählen.')
    items=[];lines=[];keys=set();hashes=set();destinations=set()
    with db() as c:
        counters={y:n for y,n in c.execute('SELECT * FROM counters')};base=counters.copy()
        for row in sorted(rows,key=lambda r:(r.get('date',''),SCANS.get(r.get('id'),{}).get('path',Path('')).name.casefold(),r.get('id',''))):
            source=SCANS.get(row['id'])
            if not source:raise ValueError('Bitte den Ordner erneut einlesen.')
            r={k:cell(row.get(k,'')) for k in ('provider','date','number','amount','account','bank')}
            if any(not r[k] for k in ('provider','date','amount','account','bank')):raise ValueError('Aussteller, Datum, Betrag und beide Konten müssen ausgefüllt sein.')
            if row.get('currency','EUR')!='EUR':raise ValueError('Nur EUR-Export möglich. Fremdwährungsbelege nicht ungeprüft übernehmen.')
            if not row.get('reviewed',False):raise ValueError('Jede ausgewählte Rechnung bitte als geprüft markieren.')
            if not r['bank'].isdigit():raise ValueError('Geldkonto darf nur Ziffern enthalten.')
            if not c.execute('SELECT 1 FROM accounts WHERE number=?',(r['account'],)).fetchone():raise ValueError('Sachkonto '+r['account']+' zuerst in der Kontenliste anlegen.')
            date=datetime.strptime(r['date'],'%Y-%m-%d')
            bookyear=preference(c,'bookyear')
            if date.year!=bookyear and not row.get('year_confirmed',False):raise ValueError('Rechnungsdatum gehört nicht zum Buchungsjahr '+str(bookyear)+'. Abweichendes Jahr beim Beleg bestätigen.')
            raw_amount=r['amount'].replace('€','').replace(' ','')
            if not re.fullmatch(r'-?(?:\d+|\d{1,3}(?:\.\d{3})+),\d{2}',raw_amount):raise ValueError('Betrag als 1234,56 eingeben.')
            amount=Decimal(raw_amount.replace('.','').replace(',','.'))
            h=source['hash']
            if digest(source['path'])!=h:raise ValueError('Quelldatei verändert. Bitte erneut einlesen.')
            key=r['provider'].casefold()+'|'+r['number'].casefold() if r['number'] else None
            if h in hashes or (key and key in keys) or c.execute('SELECT 1 FROM processed WHERE hash=? OR invoice_key=?',(h,key)).fetchone():raise ValueError('Doppelte oder bereits exportierte Rechnung: '+(r['number'] or source['path'].name))
            hashes.add(h)
            if key:keys.add(key)
            year=bookyear;counters[year]=counters.get(year,0)+1
            digits=int(s['year_digits']);yearpart='' if digits==0 else str(year)[-digits:]
            internal=cell(s['prefix'])+yearpart+str(counters[year]).zfill(int(s['sequence_digits']))
            tsv_number=internal if s.get('number_source','internal')=='internal' else r['number']
            if not tsv_number:raise ValueError('Für den Export mit Originalnummer muss die Rechnungsnummer ausgefüllt sein.')
            if '{rechnungsnummer}' in s['filename_pattern'] and not r['number']:raise ValueError('Das Dateinamensschema benötigt eine Original-Rechnungsnummer.')
            name=s['filename_pattern'].format(belegnummer=internal,rechnungsnummer=r['number'],aussteller=r['provider'],datum=r['date'],jahr=str(year)[-2:],jahr4=str(year))
            name=safe(name)
            if not name.lower().endswith('.pdf'):name+='.pdf'
            if len(name)>180:raise ValueError('Dateiname zu lang. Rechnungsstellername kürzen.')
            folder=target/date.strftime('%Y')/date.strftime('%m') if s.get('monthly',True) else target
            dest=folder/name
            if dest.exists() or str(dest).casefold() in destinations:raise ValueError('Zieldatei existiert bereits: '+str(dest))
            destinations.add(str(dest).casefold())
            lines.append(['Ausgabe',date.strftime('%d.%m.%Y'),tsv_number,r['provider'],f'{amount:.2f}'.replace('.',',')+' €','NULL',r['account'],r['bank']])
            r.update(internal=internal,year=year,sequence=counters[year],currency='EUR')
            items.append(dict(source=str(source['path']),destination=str(dest),hash=h,key=key,metadata=r))
    stream=io.StringIO(newline='');csv.writer(stream,delimiter='\t',lineterminator='\r\n').writerows(lines)
    plan_id=secrets.token_hex(16)
    export=target/('WISO_Ausgaben_'+datetime.now().strftime('%Y-%m-%d_%H%M%S')+'_'+plan_id[:6]+'.tsv')
    plan=dict(items=items,tsv=stream.getvalue(),export=str(export),settings=s,counters=counters,base=base,data=str(DATABASE.resolve()))
    PLANS.clear();PLANS[plan_id]=plan
    return {k:plan[k] for k in ('items','tsv','export')}|{'id':plan_id}

def execute(plan_id):
    plan=PLANS.pop(plan_id,None)
    if not plan or (DATABASE is None or plan['data']!=str(DATABASE.resolve())):raise ValueError('Vorschau abgelaufen. Bitte neu erstellen.')
    c=db();created=[]
    try:
        c.execute('BEGIN IMMEDIATE')
        current={y:n for y,n in c.execute('SELECT * FROM counters')}
        if current!=plan['base']:raise ValueError('Nummernstand geändert. Bitte neue Vorschau erstellen.')
        for i in plan['items']:
            if c.execute('SELECT 1 FROM processed WHERE hash=? OR invoice_key=?',(i['hash'],i['key'])).fetchone():raise ValueError('Rechnung wurde bereits exportiert.')
            if digest(Path(i['source']))!=i['hash']:raise ValueError('Quelldatei verändert.')
            dest=Path(i['destination']);dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as out:
                created.append(dest);out.write(Path(i['source']).read_bytes());out.flush();os.fsync(out.fileno())
            if digest(dest)!=i['hash']:raise ValueError('Kopierprüfung fehlgeschlagen.')
        export=Path(plan['export']);export.parent.mkdir(parents=True,exist_ok=True)
        with export.open('xb') as out:
            created.append(export);out.write(plan['tsv'].encode('utf-8'));out.flush();os.fsync(out.fileno())
        for i in plan['items']:
            c.execute('INSERT INTO processed (hash,invoice_key,destination,export,source,created,metadata) VALUES (?,?,?,?,?,?,?)',(i['hash'],i['key'],i['destination'],str(export),i['source'],datetime.now().isoformat(),json.dumps(i['metadata'],ensure_ascii=False)))
        for year,number in plan['counters'].items():c.execute('INSERT OR REPLACE INTO counters VALUES (?,?)',(year,number))
        c.commit()
    except Exception:
        c.rollback()
        for path in reversed(created):path.unlink(missing_ok=True)
        raise
    finally:c.close()
    warnings=[]
    for i in plan['items']:
        try:
            path=Path(i['source'])
            if digest(path)!=i['hash']:raise ValueError('Original inzwischen verändert')
            path.unlink()
        except Exception as e:warnings.append(i['source']+': Original blieb erhalten ('+str(e)+').')
    try:save_settings(plan['settings'])
    except Exception as e:warnings.append('Einstellungen nicht gespeichert: '+str(e))
    return dict(export=plan['export'],count=len(plan['items']),warnings=warnings)

def history():
    with db() as c:
        return [dict(id=h,**(json.loads(m) if m else {'provider':'Altimport 1.x','internal':'','date':''}),destination=d,export=e,created=t) for h,m,d,e,t in c.execute('SELECT hash,metadata,destination,export,created FROM processed ORDER BY created DESC')]

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def respond(self,obj,status=200,kind='application/json; charset=utf-8'):
        data=obj if isinstance(obj,bytes) else json.dumps(obj,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
    def trusted(self):return self.headers.get('Host')==f'127.0.0.1:{self.server.server_port}'
    def do_GET(self):
        if not self.trusted():return self.respond({'error':'Host abgelehnt'},403)
        try:
            parsed=urlparse(self.path)
            if parsed.path=='/':return self.respond((ROOT/'index.html').read_bytes(),kind='text/html; charset=utf-8')
            if parsed.path=='/api/init':return self.respond(dict(token=TOKEN,settings=settings()))
            if parsed.path=='/api/pdf':
                q=parse_qs(parsed.query)
                if q.get('token',[''])[0]!=TOKEN:return self.respond({},403)
                item=SCANS.get(q.get('id',[''])[0]);path=item['path'] if item else None
                if not path:
                    with db() as c:
                        result=c.execute('SELECT destination FROM processed WHERE hash=?',(q.get('id',[''])[0],)).fetchone()
                        if result:path=Path(result[0])
                if path and path.exists():return self.respond(path.read_bytes(),kind='application/pdf')
                raise ValueError('PDF unter dem gespeicherten Pfad nicht vorhanden. Auf anderen Rechnern kann der Ablagepfad abweichen.')
            return self.respond({},404)
        except Exception as e:return self.respond({'error':str(e)},400)
    def do_POST(self):
        if not self.trusted() or self.headers.get('X-Token')!=TOKEN or self.headers.get('Origin') not in (None,f'http://127.0.0.1:{self.server.server_port}'):return self.respond({},403)
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n>4_000_000:raise ValueError('Anfrage zu groß.')
            p=json.loads(self.rfile.read(n))
            if self.path=='/api/scan':r=scan(p['input'])
            elif self.path=='/api/reprocess':r=reprocess(p)
            elif self.path=='/api/plan':r=make_plan(p)
            elif self.path=='/api/execute':r=execute(p['id'])
            elif self.path=='/api/settings':r=save_settings(p)
            elif self.path=='/api/account':r=save_account(p)
            elif self.path=='/api/rule':r=save_rule(p)
            elif self.path=='/api/year/open':r=open_year(p)
            elif self.path=='/api/year/new':r=new_year(p)
            elif self.path=='/api/history':r=history()
            elif self.path=='/api/text':r={'text':SCANS[p['id']]['text']}
            elif self.path=='/api/browse':
                import tkinter as tk
                from tkinter import filedialog
                root=tk.Tk();root.withdraw();root.attributes('-topmost',True)
                try:
                    if p.get('save_year'):value=filedialog.asksaveasfilename(title='Neue Jahresdatei',defaultextension='.belegdb',initialfile='Belege-'+str(p.get('year',''))+'.belegdb',filetypes=[('Belegimport-Jahresdatei','*.belegdb')])
                    elif p.get('year_file'):value=filedialog.askopenfilename(title='Jahresdatei / Vorlage auswählen',filetypes=[('Belegimport-Dateien','*.belegdb *.sqlite'),('Alle','*')])
                    elif p.get('file'):value=filedialog.askopenfilename(title='Tesseract auswählen',filetypes=[('Programm','*.exe'),('Alle','*')])
                    else:value=filedialog.askdirectory(title='Ordner auswählen')
                    r={'path':value}
                finally:root.destroy()
            else:return self.respond({},404)
            self.respond(r)
        except Exception as e:self.respond({'error':str(e)},400)

if __name__=='__main__':
    config=load_json(LOCAL,{})
    if config.get('year_file'):
        try:
            check_year_file(Path(config['year_file']));DATABASE=Path(config['year_file'])
        except Exception as e:print('Letzte Jahresdatei konnte nicht geöffnet werden: '+str(e))
    server=HTTPServer(('127.0.0.1',0),Handler)
    url=f'http://127.0.0.1:{server.server_port}'
    print('BelegLotse '+(ROOT/'VERSION').read_text().strip()+': '+url+'\nNur auf einem Rechner gleichzeitig verwenden. Zum Beenden Strg+C drücken.')
    webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
