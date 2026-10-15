# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Lorenz Uhlig
"""Lokale Texterkennung und nachvollziehbare Feldregeln, ohne Cloud-Modell."""
import re, shutil, subprocess, tempfile, os, csv, io
from pathlib import Path
from collections import OrderedDict
import hashlib
RAW_CACHE=OrderedDict()
CACHE_LIMIT=32
from pypdf import PdfReader
from pypdf.errors import DependencyError
from document_model import read_geometry, text_document, make_rows
from field_engine import recognize, apply_assignments
from party_engine import analyze as analyze_parties

def norm(s): return re.sub(r'[\W_]+', ' ', s).strip().casefold()

def tesseract_path(config=''):
    if config and Path(config).is_file(): return str(Path(config))
    found=shutil.which('tesseract')
    if found:return found
    for env in ('ProgramFiles','ProgramFiles(x86)','LOCALAPPDATA'):
        for tail in ('Tesseract-OCR/tesseract.exe','Programs/Tesseract-OCR/tesseract.exe'):
            p=Path(os.environ.get(env,''))/tail
            if p.is_file():return str(p)
    return ''

def safe_layout_lines(plain,positioned):
    """Keep individual spatial lines only if their tokens exist in original text.

    Protect numbers and words from spaces inserted by layout extraction. Checking
    a whole page would discard valid header fields because of unrelated tables.
    """
    token_pattern=r'\w+(?:[.,/\-]\w+)*'
    original=set(re.findall(token_pattern,plain))
    return [line for line in (positioned or '').splitlines()
            if line.strip() and set(re.findall(token_pattern,line))<=original]

def pdf_text(path, ocr=True, tess='', with_layout=False, with_document=False):
    try:
        reader=PdfReader(path)
        if reader.is_encrypted and not reader.decrypt(''):
            raise ValueError('Öffnungspasswort erforderlich. Bitte eine entsperrte Kopie verwenden.')
    except DependencyError as e:
        raise ValueError('cryptography fehlt. App über Start.cmd starten, um die Abhängigkeit einzurichten.') from e
    texts=[];layout_lines=[];ocr_rows={}
    for page in reader.pages:
        plain=page.extract_text() or ''
        try:
            positioned=page.extract_text(extraction_mode='layout',layout_mode_space_vertically=False)
            layout_lines.extend(safe_layout_lines(plain,positioned))
            # Layout extraction may insert spaces inside words/numbers in some PDFs.
            # Use it only when it preserves the original meaningful tokens.
            tokens=set(re.findall(r'[\w./-]{4,}',plain))
            layout_tokens=set(re.findall(r'[\w./-]{4,}',positioned or ''))
            intact=not tokens or len(tokens & layout_tokens)/len(tokens)>=0.98
            texts.append(positioned if positioned and positioned.strip() and intact else plain)
        except Exception:
            texts.append(plain)
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
                            r=subprocess.run([exe,str(png),'stdout','-l',language,'--psm','3','tsv'],capture_output=True,timeout=120,check=True)
                            words=[]
                            for word in csv.DictReader(io.StringIO(r.stdout.decode('utf-8',errors='replace')),delimiter='\t'):
                                if word.get('level')!='5' or not word.get('text','').strip():continue
                                x,y,w,h=(float(word[k])/3 for k in ('left','top','width','height'))
                                words.append(dict(text=word['text'],box=[x,y,x+w,y+h],origin='ocr',confidence=float(word.get('conf',0))))
                            ocr_rows[i+1]=make_rows(words,i+1)
                            texts[i]='\n'.join(row['text'] for row in ocr_rows[i+1])
                    notes.append('OCR verwendet. Zahlen und Rechnungsnummer besonders prüfen.')
                finally:document.close()
            except Exception as e:notes.append('OCR konnte nicht abgeschlossen werden: '+str(e))
    result=('\n\n'.join(texts),notes)
    if with_document:
        try:geometry=read_geometry(path)
        except Exception:geometry=None
        if geometry:
            for page_no,rows in ocr_rows.items():
                geometry['rows']=[r for r in geometry['rows'] if r['page']!=page_no]+rows
            geometry['rows'].sort(key=lambda r:(r['page'],r['box'][1]))
        return result+(layout_lines,geometry)
    return result+(layout_lines,) if with_layout else result

def label_list(value):
    if isinstance(value,str):value=value.splitlines()
    return list(dict.fromkeys(str(x).strip() for x in (value or []) if str(x).strip()))

def provider_matches(text,rules,own_vat=(),own_tax=(),tax_country="",document=None):
    party_data=analyze_parties(text,document,own_vat,own_tax,tax_country)
    identifiers=party_data['identifiers']
    sellers=[p['name'] for p in party_data['parties'] if p['role']=='seller' and p['name']]
    available={kind:{r["key"] for r in identifiers if r["kind"]==kind and not r["own"] and not r["recipient"] and r["issuer_usable"] and r["country"]} for kind in ("vat","tax")}
    normalized=norm(text)
    def contains(term):
        return bool(re.search(r'(?<!\w)'+re.escape(norm(term))+r'(?!\w)',normalized))
    def issuer_term(term):
        if not document:return True
        occurrences=[r for r in document['rows'] if re.search(r'(?<!\w)'+re.escape(norm(term))+r'(?!\w)',norm(r['text']))]
        if not occurrences:return True
        for row in occurrences:
            blocked=any(p['role'] not in ('seller','billing') and norm(term) in norm(p['name']) and p['page']==row['page'] and -2<=row['box'][1]-p['box'][1]<=28 for p in party_data['parties'])
            if not blocked:return True
        return False
    results=[]
    for name,rule in rules.items():
        aliases=label_list(rule.get('aliases',[]))
        exclusions=label_list(rule.get('exclude',[]))
        found=[a for a in aliases if contains(a) and issuer_term(a)]
        missing=[a for a in aliases if a not in found]
        excluded=[a for a in exclusions if contains(a)]
        mode=rule.get('match_mode','any')
        permitted=available
        if rule.get('collective'):
            # Explicit opt-in for seller/platform consolidation, never own/recipient IDs.
            permitted={kind:{i['key'] for i in identifiers if i['kind']==kind and i['country'] and not i['own'] and not i['recipient'] and (i['issuer_usable'] or 'platform' in i['roles'])} for kind in ('vat','tax')}
        id_found=[v for v in rule.get('vat_ids',[]) if v in permitted['vat']]+[v for v in rule.get('tax_ids',[]) if v in permitted['tax']]
        matches=bool(aliases) and (not missing if mode=='all' else bool(found)) and not excluded
        seller_match=any(re.search(r'(?<!\w)'+re.escape(norm(term))+r'(?!\w)',norm(seller)) for term in [name]+aliases if term for seller in sellers)
        shared=[v for v in id_found if sum(v in other.get('vat_ids',[])+other.get('tax_ids',[]) for other in rules.values())>1]
        if sellers and not rule.get('collective'):
            matches=matches and seller_match
            id_found=[v for v in id_found if (v not in shared or seller_match) and (any(i['key']==v and 'seller' in i['roles'] for i in identifiers) or seller_match)]
        elif shared and not matches:
            id_found=[v for v in id_found if v not in shared]
        ignored=[i['key'] for i in identifiers if i['key'] in rule.get('vat_ids',[])+rule.get('tax_ids',[]) and i['key'] not in id_found]
        results.append(dict(name=name,mode=mode,found=found,missing=missing,excluded=excluded,matched=matches,id_found=id_found,id_match=bool(id_found) and not excluded,ignored_ids=ignored,seller_match=seller_match,parties=sellers))
    return results

def extract_fields(text,rules,selected_provider=None,own_vat=(),own_tax=(),tax_country="",layout_lines=(),document=None):
    notes=[];provider=''
    evidence=provider_matches(text,rules,own_vat,own_tax,tax_country,document)
    strong=[r["name"] for r in evidence if r["id_match"]]
    matched=strong or [r['name'] for r in evidence if r['matched']]
    for item in evidence:
        item['matched']=item['name'] in matched
    if selected_provider is not None:
        provider=selected_provider
        notes.append('Rechnungssteller manuell ausgewählt: '+provider+'. Feldregeln erneut angewendet.')
    elif len(matched)==1:
        provider=matched[0]
        found=next((r['id_found'] if strong else r['found']) for r in evidence if r['name']==provider)
        notes.append('Rechnungssteller erkannt: '+provider+'; '+('bestätigte Kennung: ' if strong else 'Texttreffer: ')+', '.join(found)+'.')
    elif len(matched)>1:
        notes.append('Mehrere Rechnungsstellerregeln passen: '+', '.join(matched)+'. Bitte auswählen.')
    else:
        notes.append('Kein gespeicherter Rechnungssteller passt. Bitte auswählen oder Rechnungssteller anlegen.')
    rule=rules.get(provider,{})
    label_map=rule.get('labels',{})
    if document is None:
        document=text_document(text)
        if layout_lines:
            extra=text_document('\n'.join(layout_lines))
            document['rows'].extend(extra['rows'])
    recognized=recognize(document,label_map)
    apply_assignments(recognized,document,rule.get('field_memory',{}))
    candidates=recognized['candidates'];field_evidence=recognized['field_evidence']
    result=recognized['values']
    for f,vs in candidates.items():
        if len(vs)==1:
            labels=list(dict.fromkeys(h['label'] for h in field_evidence[f] if h['selected']))
            notes.append({'date':'Datum','number':'Rechnungsnummer','amount':'Betrag'}[f]+' aus „'+' / '.join(labels)+'“: '+vs[0]+'.')
        if len(vs)>1:notes.append({'date':'Datum','number':'Rechnungsnummer','amount':'Betrag'}[f]+' mehrdeutig: '+', '.join(vs)+'. Bitte auswählen/eintragen.')
    for f,status in recognized['field_status'].items():
        if status=='review':notes.append({'date':'Datum','number':'Rechnungsnummer','amount':'Betrag'}[f]+' ist ein Vorschlag mit schwächerer Fundstelle; bitte prüfen.')
    if not text.strip():notes.append('Kein Text erkannt. Werte bitte manuell erfassen.')
    for f in ('date','amount'):
        if not result[f]:notes.append({'date':'Rechnungsdatum','amount':'Rechnungssumme'}[f]+' fehlt oder ist unklar.')
    currency='EUR'
    foreign=re.findall(r'\b(?:USD|GBP|CHF|CAD|AUD|JPY|SEK|NOK|DKK)\b',text)
    if foreign:currency=foreign[0];notes.append('Fremdwährung erwähnt. Dieser TSV-Export unterstützt nur EUR; Betrag/Währung vor Export klären.')
    result.update(provider=provider,currency=currency,note=' '.join(notes),candidates=candidates,field_evidence=field_evidence,field_status=recognized['field_status'],provider_matches=evidence,**analyze_parties(text,document,own_vat,own_tax,tax_country))
    return result

def extract(path,rules=None,ocr=True,tess='',own_vat=(),own_tax=(),tax_country='',fingerprint=None):
    fingerprint=fingerprint or hashlib.sha256(Path(path).read_bytes()).hexdigest()
    key=(fingerprint,bool(ocr),tess)
    if key in RAW_CACHE:
        text,notes,layout_lines,document=RAW_CACHE[key];RAW_CACHE.move_to_end(key)
    else:
        read=pdf_text(path,ocr,tess,with_layout=True,with_document=True)
        text,notes,layout_lines=read[:3]
        document=read[3] if len(read)>3 else None
        if not any('OCR nötig' in n or 'OCR konnte nicht' in n for n in notes):
            RAW_CACHE[key]=(text,notes,layout_lines,document)
        while len(RAW_CACHE)>CACHE_LIMIT:RAW_CACHE.popitem(last=False)
    result=extract_fields(text,rules or {},own_vat=own_vat,own_tax=own_tax,tax_country=tax_country,layout_lines=layout_lines,document=document)
    result['document']=document
    result['note']=' '.join(notes+[result['note']]).strip()
    result['read_notes']=notes
    result['layout_lines']=layout_lines
    result['text']=text
    return result
