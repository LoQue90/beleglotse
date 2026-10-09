# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Lorenz Uhlig
"""Lokale Texterkennung und nachvollziehbare Feldregeln, ohne Cloud-Modell."""
import re, shutil, subprocess, tempfile, os
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from pypdf import PdfReader
from pypdf.errors import DependencyError

DATE = r'\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})\b'
MONEY = r'(?<![\w\d])[-−]?(?:\d{1,3}(?:[. ,\u00a0]\d{3})+|\d+)[.,]\d{2}(?!\d)'

def norm(s): return re.sub(r'\s+', ' ', s).strip().casefold()

def tesseract_path(config=''):
    if config and Path(config).is_file(): return str(Path(config))
    found=shutil.which('tesseract')
    if found:return found
    for env in ('ProgramFiles','ProgramFiles(x86)','LOCALAPPDATA'):
        for tail in ('Tesseract-OCR/tesseract.exe','Programs/Tesseract-OCR/tesseract.exe'):
            p=Path(os.environ.get(env,''))/tail
            if p.is_file():return str(p)
    return ''

def pdf_text(path, ocr=True, tess=''):
    try:
        reader=PdfReader(path)
        if reader.is_encrypted and not reader.decrypt(''):
            raise ValueError('Öffnungspasswort erforderlich. Bitte eine entsperrte Kopie verwenden.')
    except DependencyError as e:
        raise ValueError('cryptography fehlt. App über Start.cmd starten, um die Abhängigkeit einzurichten.') from e
    texts=[p.extract_text() or '' for p in reader.pages]
    missing=[i for i,t in enumerate(texts) if len(re.sub(r'\W','',t))<40]
    notes=[]
    if missing:
        exe=tesseract_path(tess) if ocr else ''
        if not ocr:notes.append('Mindestens eine Seite hat wenig Text. OCR ist ausgeschaltet.')
        elif not exe:notes.append('OCR nötig: Tesseract fehlt. Unter Einstellungen den Pfad zu tesseract.exe angeben oder Tesseract installieren.')
        else:
            try:
                import pypdfium2 as pdfium
                langs=subprocess.run([exe,'--list-langs'],capture_output=True,text=True,timeout=20,check=True).stdout
                language='+'.join(x for x in ('deu','eng') if x in langs.split())
                if not language:raise ValueError('Tesseract-Sprachdaten deu oder eng fehlen.')
                document=pdfium.PdfDocument(str(path),password='')
                try:
                    with tempfile.TemporaryDirectory() as tmp:
                        for i in missing:
                            page=document[i]
                            try:
                                bitmap=page.render(scale=3)
                                try:
                                    image=bitmap.to_pil();png=Path(tmp)/'page.png';image.save(png);image.close()
                                finally:bitmap.close()
                            finally:page.close()
                            r=subprocess.run([exe,str(png),'stdout','-l',language,'--psm','3'],capture_output=True,timeout=120,check=True)
                            texts[i]=r.stdout.decode('utf-8',errors='replace')
                    notes.append('OCR verwendet. Zahlen und Rechnungsnummer besonders prüfen.')
                finally:document.close()
            except Exception as e:notes.append('OCR konnte nicht abgeschlossen werden: '+str(e))
    return '\n\n'.join(texts),notes

def date_value(s):
    for fmt in ('%Y-%m-%d','%d.%m.%Y','%d-%m-%Y','%d/%m/%Y'):
        try:return datetime.strptime(s,fmt).date().isoformat()
        except ValueError:pass
    return ''

def money_value(s):
    s=re.sub(r'[\s\u00a0]','',s).replace('−','-')
    decimal=max(s.rfind(','),s.rfind('.'))
    if decimal<0:return ''
    s=re.sub(r'[.,]','',s[:decimal])+'.'+s[decimal+1:]
    try:return f'{Decimal(s):.2f}'.replace('.',',')
    except Exception:return ''

def label_list(value):
    if isinstance(value,str):value=value.splitlines()
    return list(dict.fromkeys(str(x).strip() for x in (value or []) if str(x).strip()))

def after_labels(text,labels,kind):
    values=[]
    pattern={'date':DATE,'number':r'[A-Za-z0-9][A-Za-z0-9._/\-]*','amount':MONEY}[kind]
    for label in labels:
        if not label.strip():continue
        # A label may be followed by a value on the same or next line.
        label_re=r'\s+'.join(re.escape(p) for p in label.strip().split())
        for m in re.finditer(r'(?<!\w)'+label_re+r'(?!\w)[ \t]*(?:[:#=][ \t]*)?',text,re.I):
            tail=text[m.end():].lstrip(' \t\r\n')
            line=tail.split('\n',1)[0][:180]
            if kind=='number':
                match=re.match(pattern,line)
                candidates=[match.group()] if match else []
            else:candidates=re.findall(pattern,line)
            for v in candidates:
                v=date_value(v) if kind=='date' else money_value(v) if kind=='amount' else v.rstrip('.')
                if v and v not in values:values.append(v)
    return values

def extract_fields(text,rules):
    notes=[];provider='';normalized=norm(text)
    matched=[]
    for name,rule in rules.items():
        # Names are not implicit keywords: rules remain explicit and editable.
        aliases=rule.get('aliases',[])
        if any(re.search(r'(?<!\w)'+re.escape(norm(a))+r'(?!\w)',normalized) for a in aliases if a.strip()):matched.append(name)
    if len(matched)==1:provider=matched[0]
    elif len(matched)>1:notes.append('Mehrere Anbieterregeln passen: '+', '.join(matched)+'. Bitte auswählen.')
    builtin=''
    if 'mollie b.v.' in normalized:builtin='Mollie'
    elif 'deutsche post' in normalized:
        builtin='DHL' if 'gesamtsumme brutto' in normalized and re.search(r'paket|päckchen',normalized) else 'Deutsche Post'
    if not provider and not matched and builtin:provider=builtin
    if not provider and not matched:
        # A company line is only a proposal, never an unmarked definitive result.
        lines=[s.strip() for s in text.splitlines() if s.strip()]
        plausible=[s for s in lines[:35] if re.search(r'\b(?:GmbH|AG|Ltd\.?|B\.V\.|UG|KG|Inc\.?)\b',s) and len(s)<100 and not re.search(r'bank|vorstand|register',s,re.I)]
        if len(plausible)==1:provider=plausible[0];notes.append('Aussteller nur vorgeschlagen; mit dem Beleg abgleichen und Anbieterregel speichern.')
        else:notes.append('Aussteller bitte auswählen/eintragen und Erkennungsmerkmal speichern.')
    rule=rules.get(provider,{})
    label_map=rule.get('labels',{})
    defaults={
        'date':['Rechnungsdatum','Belegdatum','Invoice date','Datum der Rechnung'],
        'number':['Rechnungsnummer','Rechnungs-Nr.','Rechnungs-Nr','Rechnung Nr.','Invoice number','Invoice no.','Belegnummer','Rechnungsreferenz'],
        'amount':['Gesamtsumme Brutto','Gesamtbetrag','Rechnungsbetrag','Endbetrag','Bruttobetrag','Total amount','Grand total','Insgesamt inklusive Mehrwertsteuer']}
    candidates={}
    for field in ('date','number','amount'):
        custom=label_list(label_map.get(field,[]))
        labels=custom or defaults[field]
        values=after_labels(text,labels,field)
        if not custom:
            if builtin=='Mollie':
                values=after_labels(text,{'date':['Rechnungsdatum'],'number':['Rechnungsreferenz'],'amount':['Insgesamt inklusive Mehrwertsteuer']}[field],field)
            elif builtin=='Deutsche Post' and 'belegnummer:' in normalized:
                values=after_labels(text,{'date':['Belegdatum'],'number':['Belegnummer'],'amount':['Betrag']}[field],field)
            elif builtin=='DHL':
                values=after_labels(text,{'date':['Rechnungsdatum'],'number':['Rechnungsnummer'],'amount':['Gesamtsumme Brutto']}[field],field)
        candidates[field]=values
    # Weak total labels are useful but must be marked for review.
    if not candidates['amount'] and not label_list(label_map.get('amount',[])):
        candidates['amount']=after_labels(text,['Gesamt','Total','Zahlbetrag'], 'amount')
        if candidates['amount']:notes.append('Betrag aus allgemeiner Summenbezeichnung vorgeschlagen; Rechnungssumme prüfen.')
    result={f:vs[0] if len(vs)==1 else '' for f,vs in candidates.items()}
    for f,vs in candidates.items():
        if len(vs)>1:notes.append({'date':'Datum','number':'Rechnungsnummer','amount':'Betrag'}[f]+' mehrdeutig: '+', '.join(vs)+'. Bitte auswählen/eintragen.')
    if builtin=='Mollie':notes.append('Mollie: Rechnungssumme, nicht offener oder verrechneter Betrag. Steuerhinweise im Beleg prüfen.')
    if not text.strip():notes.append('Kein Text erkannt. Werte bitte manuell erfassen.')
    for f in ('date','amount'):
        if not result[f]:notes.append({'date':'Rechnungsdatum','amount':'Rechnungssumme'}[f]+' fehlt oder ist unklar.')
    currency='EUR'
    foreign=re.findall(r'\b(?:USD|GBP|CHF|CAD|AUD|JPY|SEK|NOK|DKK)\b',text)
    if foreign:currency=foreign[0];notes.append('Fremdwährung erwähnt. Dieser TSV-Export unterstützt nur EUR; Betrag/Währung vor Export klären.')
    result.update(provider=provider,currency=currency,note=' '.join(notes),candidates=candidates)
    return result

def extract(path,rules=None,ocr=True,tess=''):
    text,notes=pdf_text(path,ocr,tess)
    result=extract_fields(text,rules or {})
    result['note']=' '.join(notes+[result['note']]).strip()
    result['text']=text
    return result
