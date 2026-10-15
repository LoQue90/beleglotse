# SPDX-License-Identifier: GPL-3.0-only
"""Explicit party roles, with no issuer-specific rules or identifier assumptions."""
import re
from identifiers import compact, find_identifiers
from document_model import text_document, span_box, rectangle

ROLE_LABELS={
 'seller':r'Verkauft\s+von|Sold\s+by|Rechnungssteller|Leistungserbringer',
 'platform':r'Umsatzsteuer\s+erklärt\s+durch|VAT\s+declared\s+by|Steuervertreter|Fiskalvertreter|Fiscal\s+(?:representative|representative\s+by)',
 'recipient':r'Rechnungsadresse|Lieferadresse|Lieferanschrift|Rechnung\s+an|Versand\s+an|Bill\s+to|Ship\s+to|Rechnungsempfänger',
 'carrier':r'Versand\s+per|Ship\s+via|Versandart',
 'insurer':r'Versicherer',
 'billing':r'Abrechnungsstelle',
}


def parties(document):
    rows=document['rows'];roles=[]
    pattern=re.compile(r'(?<!\w)(?:'+'|'.join('(?P<'+k+'>'+v+')' for k,v in ROLE_LABELS.items())+r')(?!\w)',re.I)
    for ri,row in enumerate(rows):
        matches=list(pattern.finditer(row['text']))
        for mi,m in enumerate(matches):
            box=span_box(row,*m.span());end=matches[mi+1].start() if mi+1<len(matches) else len(row['text'])
            # A wide word gap marks the next column, even without a role heading.
            column_end=10000
            for left,right in zip(row['words'],row['words'][1:]):
                if left['end']>=m.end() and right['box'][0]-left['box'][2]>max(18,(left['box'][3]-left['box'][1])*2):
                    column_end=right['box'][0]-3;end=min(end,right['start']);break
            name=row['text'][m.end():end].strip(' :')
            name_box=span_box(row,m.end(),end) if name else None
            if not name:
                next_x=span_box(row,*matches[mi+1].span())[0] if mi+1<len(matches) else column_end
                for below in rows[ri+1:ri+4]:
                    if below['page']!=row['page'] or below['box'][1]-row['box'][3]>24:break
                    words=[w for w in below['words'] if box[0]-8<=w['box'][0]<next_x-3]
                    if words:
                        name=' '.join(w['text'] for w in words);name_box=[words[0]['box'][0],below['box'][1],words[-1]['box'][2],below['box'][3]];break
            # A party name should not be a following field heading or address-only line.
            if re.match(r'(?:Rechnungsdatum|Invoice date|\d|USt[.-]|VAT)',name,re.I):name=''
            roles.append(dict(role=m.lastgroup,name=name,page=row['page'],box=box,name_box=name_box,row=ri,label=m.group(),end_x=column_end))
    return roles


def identifier_box(row,value):
    target=compact(value)
    for start in range(len(row['words'])):
        joined=''
        for end in range(start,min(start+10,len(row['words']))):
            word=row['words'][end]
            if end>start and word['box'][0]-row['words'][end-1]['box'][2]>18:break
            joined+=compact(word['text'])
            if target==joined or (end==start and target in joined):
                return rectangle(row['words'][start:end+1])
            if len(joined)>=len(target):break
    return None


def analyze(text,document=None,own_vat=(),own_tax=(),tax_country=''):
    document=document or text_document(text);roles=parties(document)
    identifiers=find_identifiers(text,own_vat,own_tax,tax_country)
    for ident in identifiers:
        locations=[]
        for ri,row in enumerate(document['rows']):
            if compact(ident['value']) not in compact(row['text']):continue
            if re.search(r'(?:Ihre|Your|Customer|Kunden|Empfänger).*?(?:USt|VAT|Steuer)',row['text'],re.I):ident['recipient']=True
            ident_box=identifier_box(row,ident['value'])
            if ident_box is None:continue
            possible=[]
            for role in roles:
                if role['page']!=row['page'] or role['row']>ri:continue
                dy=row['box'][1]-role['box'][1]
                if dy>90:continue
                # Match the identifier's own word column, not the entire merged row.
                x=ident_box[0]
                if x<role['box'][0]-12 or x>=role['end_x'] or x-role['box'][0]>230:continue
                possible.append((dy+abs(x-role['box'][0])*.08,role))
            best=min(possible,key=lambda x:x[0])[1] if possible else None
            locations.append(dict(page=row['page'],box=ident_box,role=best['role'] if best else 'unknown',name=best['name'] if best else ''))
        active_roles={loc['role'] for loc in locations}
        ident['roles']=sorted(active_roles);ident['locations']=locations
        ident['issuer_usable']=not ident['own'] and not ident['recipient'] and (not active_roles or bool(active_roles & {'seller','unknown'}))
        ident['reason']='Kennung in einem Verkäuferbereich' if 'seller' in active_roles else 'Kennung ohne eindeutige Rollenbeschriftung' if ident['issuer_usable'] else 'Eigene/Empfängerkennung oder Kennung einer anderen beteiligten Stelle'
    return dict(parties=roles,identifiers=identifiers)
