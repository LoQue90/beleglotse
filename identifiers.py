# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Lorenz Uhlig
"""Conservative identifier candidates and geometric company-name proposals."""
import re
from pypdf import PdfReader

VAT_LABEL = r'(?:USt[.\s-]*(?:Id(?:entifikations)?[.\s-]*(?:Nr\.?)?|ID)|Umsatzsteuer[\s-]*(?:ID|Identifikationsnummer)|VAT\s*(?:ID|No\.?|Number|Registration)?)'
TAX_LABEL = r'(?:Steuer[\s-]*(?:nummer|Nr\.?)|St[.\s-]*Nr\.?|Tax\s*(?:number|no\.?))'
COMPANY = re.compile(r'\b(?:GmbH|AG|B\.V\.|Ltd\.?|Limited|Inc\.?|LLC|KG|UG|S\.A\.)\b',re.I)

def compact(value):return re.sub(r'[^A-Z0-9]','',str(value).upper())
def vat(value):
    result=compact(value)
    if not re.fullmatch(r'[A-Z]{2}[A-Z0-9]{7,14}',result) or not any(c.isdigit() for c in result):
        raise ValueError('USt-ID mit Länderpräfix eingeben, z. B. DE123456789.')
    if result.startswith('DE') and not re.fullmatch(r'DE\d{9}',result):raise ValueError('Deutsche USt-ID: DE und neun Ziffern erforderlich.')
    return result

def tax(value):
    parts=str(value).strip().split(':',1)
    if len(parts)!=2 or not re.fullmatch(r'[A-Za-z]{2}',parts[0].strip()):
        raise ValueError('Steuernummer mit Land eingeben: DE:123/456/78901.')
    digits=compact(parts[1]);country=parts[0].strip().upper()
    if not re.fullmatch(r'\d{5,16}',digits):raise ValueError('Steuernummer muss 5 bis 16 Ziffern enthalten.')
    return country+':'+digits

def entries(value,kind):
    source=value.splitlines() if isinstance(value,str) else (value or [])
    normalize=vat if kind=='vat' else tax
    return list(dict.fromkeys(normalize(x) for x in source if str(x).strip()))

def find_identifiers(text,own_vat=(),own_tax=(),tax_country=''):
    records=[];seen=set()
    def add(kind,value,start,end,country=''):
        key=(kind,country,value)
        if key in seen:return
        seen.add(key)
        context=text[max(0,start-120):min(len(text),end+140)].strip()
        # Explicit recipient labels are evidence against automatic issuer assignment.
        before=text[max(0,start-65):start]
        recipient=bool(re.search(r'(?:Ihre|Your|Customer|Kunden|Empfänger)[^\n]{0,35}$',before,re.I))
        canonical=value if kind=='vat' else country+':'+value
        own=canonical in (own_vat if kind=='vat' else own_tax) or (kind=='tax' and not country and any(v.split(':',1)[-1]==value for v in own_tax))
        records.append(dict(kind=kind,value=value,country=country,key=canonical,context=context,own=own,recipient=recipient))
    # German IDs can be anywhere, also with embedded whitespace/dashes.
    for m in re.finditer(r'(?<!\w)DE[ \t\r\n.-]*(?:\d[ \t.-]*){8}\d(?![ \t.-]*\d)',text,re.I):
        add('vat',compact(m.group()),m.start(),m.end(),'DE')
    # Other formats are only proposed when explicitly labelled.
    for m in re.finditer(VAT_LABEL+r'\s*[:#.]?\s*',text,re.I):
        tail=text[m.end():].splitlines()[:2]
        for line in tail:
            candidate=re.match(r'([A-Za-z]{2}[ \t.-]*[A-Za-z0-9][A-Za-z0-9 .-]{5,22})',line.strip())
            if not candidate:continue
            try:value=vat(candidate.group(1).strip())
            except ValueError:continue
            add('vat',value,m.start(),m.end()+len(candidate.group()),value[:2]);break
    countries={r['country'] for r in records if not r['own'] and not r['recipient']}
    country=next(iter(countries)) if len(countries)==1 else tax_country.upper().strip()
    if not country:
        if re.search(r'\b(?:Deutschland|Germany)\b',text,re.I):country='DE'
    for m in re.finditer(TAX_LABEL+r'[ \t]*[:#.]?[ \t]*(?:\r?\n[ \t]*)?([0-9][0-9 /.-]{4,24})',text,re.I):
        value=compact(m.group(1))
        if re.fullmatch(r'\d{5,16}',value):add('tax',value,m.start(),m.end(),country)
    return records

def company_names(text):
    result=[]
    for line in text.splitlines():
        line=line.strip()
        if not 3<=len(line)<=100 or not COMPANY.search(line):continue
        if re.search(r'(?:Datenschutz|übermittel|Abrechnung sind|Fragen|IBAN|Vorstand|Registergericht)',line,re.I):continue
        # Limit to the legal name, excluding following street addresses.
        match=COMPANY.search(line);name=line[:match.end()].strip(' ,*')
        if name and name not in result:result.append(name)
    return result[:12]

def layout_candidates(path,records):
    """Match identifiers to nearby company blocks, retaining ambiguous alternatives."""
    reader=PdfReader(path)
    if reader.is_encrypted:reader.decrypt('')
    blocks=[]
    for page_number,page in enumerate(reader.pages,1):
        def visitor(text,cm,tm,font,size):
            if not text.strip():return
            x=tm[4]*cm[0]+tm[5]*cm[2]+cm[4];y=tm[4]*cm[1]+tm[5]*cm[3]+cm[5]
            for i,line in enumerate(text.splitlines()):
                if line.strip():blocks.append(dict(text=line.strip(),x=x,y=y-i*max(float(size),1)*1.2,page=page_number))
        page.extract_text(visitor_text=visitor)
    companies=[(b,n) for b in blocks for n in company_names(b['text'])]
    result={}
    for record in records:
        matches=[b for b in blocks if compact(record['value']) in compact(b['text'])]
        ranked=[]
        for loc in matches:
            nearby=[]
            for b,name in companies:
                if b['page']!=loc['page']:continue
                dx=abs(b['x']-loc['x']);dy=b['y']-loc['y']
                # Footer columns: issuer usually above identifier, same column.
                distance=dx*4+abs(dy)+(160 if dy<0 else 0)
                nearby.append((distance,name,b,loc))
            ranked.extend(sorted(nearby,key=lambda x:x[0])[:3])
        ranked.sort(key=lambda x:x[0]);names=[]
        for score,name,b,loc in ranked:
            if name not in names:names.append(name)
        result[(record['kind'],record['key'])]=dict(names=names[:3],page=ranked[0][3]['page'] if ranked else None,reason='Firmenname räumlich nahe der Kennung (Vorschlag, bitte prüfen).' if ranked else 'Keine räumliche Zuordnung verfügbar; Textvorschläge prüfen.')
    return result
