# SPDX-License-Identifier: GPL-3.0-only
"""Generic semantic field recognition over positioned document rows.

No issuer names, identifiers, filenames or fixed template coordinates belong here.
Every proposal retains its printed source; arithmetic only corroborates it.
"""
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from document_model import span_box, text_document

MONTHS = {'jan':1,'januar':1,'january':1,'feb':2,'februar':2,'february':2,
          'mär':3,'märz':3,'maerz':3,'mar':3,'march':3,'apr':4,'april':4,
          'mai':5,'may':5,'jun':6,'juni':6,'june':6,'jul':7,'juli':7,'july':7,
          'aug':8,'august':8,'sep':9,'sept':9,'september':9,'okt':10,'oktober':10,'oct':10,'october':10,
          'nov':11,'november':11,'dez':12,'dezember':12,'dec':12,'december':12}
MONTH = '(?:'+'|'.join(sorted(MONTHS,key=len,reverse=True))+')'
DATE = r'(?<!\w)(?:\d{4}-\d{2}-\d{2}|\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4}|\d{1,2}[.\s\-]+'+MONTH+r'[.\s\-]+(?:\d{4}|\d{2})|'+MONTH+r'\s+\d{1,2},?\s+\d{4})(?!\w)'
MONEY = r'(?<![\w\d])[-−]?(?:\d{1,3}(?:[. ,\u00a0]\d{3})+|\d+)[.,]\d{2}(?!\d)(?:[-−](?!\d))?'
NUMBER = r'(?<!\w)[A-Za-z0-9][A-Za-z0-9._/\-]*(?!\w)'
# role -> (strength, synonyms). Lower strengths remain explicit review proposals.
LEXICON = {
 'date':(90,['Rechnungsdatum','Rechnungs Datum','Belegdatum','Invoice date','Datum der Rechnung','Ausstellungsdatum']),
 'date_generic':(60,['Datum','Erstellt am']),
 'number':(90,['Rechnungsnummer','Rechnungs-Nr','Rechnungs Nr','Rechnungsnr','Rechnung Nr','Invoice number','Invoice no','Belegnummer','Beleg Nr','Rechnungsreferenz','DSD-Belegnummer']),
 'number_generic':(60,['Rechnung']),
 'amount':(100,['Rechnungsbetrag inklusive Umsatzsteuer','Gesamtsumme Brutto','Gesamtbetrag','Rechnungsbetrag','Endbetrag','Bruttobetrag','Bruttowert','Gesamtpreis Brutto','Total amount','Grand total','Insgesamt inklusive Mehrwertsteuer']),
 'amount_payable':(90,['Zahlbetrag','Zu zahlender Gesamtbetrag']),
 'amount_generic':(60,['Gesamt','Total','Betrag','Gesamtpreis','Gesamtsumme']),
 'amount_prepaid':(45,['Vorausbezahlt','Prepaid','Mit Kreditkarte bezahlt','Paid by credit card']),
 'net':(0,['Rechnungsbetrag ohne Umsatzsteuer','Nettobetrag','Nettowert','Netto','Gesamtpreis Netto','Warenwert','Merchandise','Subtotal','Zwischensumme']),
 'tax':(0,['Umsatzsteuer','UStbetrag','USt','MwSt','VAT','Versicherungssteuer','Enthaltene USt']),
 'due':(0,['Fälliger Betrag','Offener Betrag','Restbetrag','Restguthaben','Amount due','Balance due','Zahlung','Verrechnungen']),
 'other_date':(0,['Bestelldatum','Lieferdatum','Fälligkeitsdatum','Order Date','Delivery Date','Abrechnungszeitraum','Versicherungszeitraum']),
 'other_number':(0,['Kundennummer','Kunden Nr','Kunden-Nummer','Auftragsnummer','Auftrag','Bestellnummer','Bestell Nr','Purchase Order No','Customer Number','Seite','Page No','Versicherungsnummer']),
}


def date_value(value):
    value=value.strip().casefold()
    try:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):return date.fromisoformat(value).isoformat()
        m=re.fullmatch(r'(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})',value)
        if m:return date(int(m[3]),int(m[2]),int(m[1])).isoformat()
        m=re.fullmatch(r'(\d{1,2})[.\s\-]+('+MONTH+r')[.\s\-]+(\d{4}|\d{2})',value)
        if m:
            year=int(m[3]);year=2000+year if len(m[3])==2 else year
            return date(year,MONTHS[m[2]],int(m[1])).isoformat()
        m=re.fullmatch('('+MONTH+r')\s+(\d{1,2}),?\s+(\d{4})',value)
        if m:return date(int(m[3]),MONTHS[m[1]],int(m[2])).isoformat()
    except (ValueError,KeyError):pass
    return ''


def money_value(value):
    value=re.sub(r'\s','',value).replace('−','-')
    if value.endswith('-'):value='-'+value[:-1]
    decimal=max(value.rfind(','),value.rfind('.'))
    if decimal<0:return ''
    value=re.sub(r'[.,]','',value[:decimal])+'.'+value[decimal+1:]
    try:return f'{Decimal(value):.2f}'.replace('.',',')
    except InvalidOperation:return ''


def label_pattern(label):
    tokens=re.findall(r'\w+',label,re.UNICODE)
    if not tokens:return r'(?!)'
    return r'(?<!\w)'+r'[\s.:/#=()\-]*'.join(re.escape(t) for t in tokens)+r'(?!\w)'


def anchors(document,custom):
    specs=[];known={}
    for role,(strength,labels) in LEXICON.items():
        for label in labels:
            known[re.sub(r'\W','',label.casefold())]=role
            specs.append((role,strength,label,re.compile(label_pattern(label),re.I)))
    for field,labels in custom.items():
        if isinstance(labels,str):labels=labels.splitlines()
        for label in labels:
            label=label.strip()
            semantic=known.get(re.sub(r'\W','',label.casefold()))
            # Existing semantics cannot accidentally be changed by a misplaced term.
            if not label or (semantic and not semantic.startswith(field)):continue
            if not semantic:specs.append((field,90 if field!='amount' else 100,label,re.compile(label_pattern(label),re.I)))
    result=[]
    for ri,row in enumerate(document['rows']):
        found=[]
        for role,strength,label,pattern in specs:
            for match in pattern.finditer(row['text']):
                found.append(dict(role=role,score=strength,label=label,start=match.start(),end=match.end(),box=span_box(row,*match.span()),row=ri,page=row['page']))
        # Long semantic labels own their span, e.g. offener Betrag / Rechnungs Datum.
        kept=[]
        for hit in sorted(found,key=lambda h: (-(h['end']-h['start']),-h['score'])):
            if not any(hit['start']<h['end'] and hit['end']>h['start'] for h in kept):kept.append(hit)
        result.extend(kept)
    # Join multi-line label fragments only in the same column and close vertically.
    # The anchor ends on the lower row, so values to its right/below use normal logic.
    if document.get('positioned'):
        for ri,row in enumerate(document['rows']):
            for below_index in range(ri+1,min(ri+3,len(document['rows']))):
                below=document['rows'][below_index]
                if below['page']!=row['page'] or below['box'][1]-row['box'][3]>15:break
                for role,strength,label,pattern in specs:
                    tokens=re.findall(r'\w+',label)
                    if len(tokens)<2:continue
                    for cut in range(1,len(tokens)):
                        first=re.compile(label_pattern(' '.join(tokens[:cut])),re.I)
                        second=re.compile(label_pattern(' '.join(tokens[cut:])),re.I)
                        for top_match in first.finditer(row['text']):
                            top_box=span_box(row,*top_match.span())
                            for lower_match in second.finditer(below['text']):
                                lower_box=span_box(below,*lower_match.span())
                                if abs(top_box[0]-lower_box[0])>18:continue
                                if top_match.end()<len(row['text']) and row['text'][top_match.end():].strip(' .:'):continue
                                if lower_match.start()>0:continue
                                result=[a for a in result if not (a['row']==ri and a['start']>=top_match.start() and a['end']<=top_match.end()) and not (a['row']==below_index and a['start']>=lower_match.start() and a['end']<=lower_match.end())]
                                result.append(dict(role=role,score=strength,label=label,start=lower_match.start(),end=lower_match.end(),box=[min(top_box[0],lower_box[0]),top_box[1],max(top_box[2],lower_box[2]),lower_box[3]],row=below_index,page=row['page']))
    return result


def values(row,kind):
    pattern={'date':DATE,'amount':MONEY,'number':NUMBER}[kind]
    dates=[m.span() for m in re.finditer(DATE,row['text'],re.I)]
    amounts=[m.span() for m in re.finditer(MONEY,row['text'])]
    for m in re.finditer(pattern,row['text'],re.I):
        raw=m.group()
        if kind!='date' and any(m.start()<b and m.end()>a for a,b in dates):continue
        if kind=='amount' and re.match(r'\s*%',row['text'][m.end():]):continue
        if kind=='number':
            if any(m.start()<b and m.end()>a for a,b in amounts):continue
            if not any(c.isdigit() for c in raw) and not (raw.isupper() and len(raw)>=2):continue
            if raw.upper() in {'EUR','USD','GBP','CHF','IBAN','UST','VAT','PDF','AG','GMBH'}:continue
        value=date_value(raw) if kind=='date' else money_value(raw) if kind=='amount' else raw.rstrip('.')
        if value:yield dict(value=value,raw=raw,start=m.start(),end=m.end(),box=span_box(row,*m.span()))


def gather(document,custom):
    rows=document['rows'];all_anchors=anchors(document,custom);result={f:[] for f in ('date','number','amount')}
    positioned=document.get('positioned',False)
    def add(anchor,row,value,relation,score=None,reason=''):
        field=anchor['role'].split('_')[0]
        if field not in result:return
        result[field].append(dict(value=value['value'],raw=value['raw'],label=anchor['label'],score=anchor['score'] if score is None else score,
            page=row['page'] if positioned else None,box=value['box'] if positioned else None,label_box=anchor['box'] if positioned else None,
            role=anchor['role'],relation=relation,context=row['text'],reason=reason or ('Wert rechts neben der Beschriftung' if relation=='right' else 'Wert unter der Beschriftung in derselben Spalte'),origin=row['words'][0].get('origin','pdf') if positioned else 'text'))
    for anchor in all_anchors:
        kind=anchor['role'].split('_')[0]
        if kind not in result:continue
        row=rows[anchor['row']];neighbors=[a for a in all_anchors if a['row']==anchor['row'] and a['start']>=anchor['end']]
        stop=min((a['start'] for a in neighbors),default=len(row['text']))
        right=[v for v in values(row,kind) if v['start']>=anchor['end'] and v['end']<=stop]
        tail=row['text'][anchor['end']:stop]
        if kind=='amount':
            if re.search(r'\b(?:netto|net|ohne|excl|excluding)\b',tail,re.I):right=[]
            if anchor['role']=='amount_generic' and right:
                prefix=row['text'][anchor['end']:right[0]['start']].strip(' :#=€\t')
                if prefix.upper() not in ('','EUR'):right=[]
        if kind=='number' and right:
            prefix=row['text'][anchor['end']:right[0]['start']].strip(' .:#=\t')
            if prefix:right=[]
        if right:
            if kind=='amount' and len(right)>1:
                # Only a printed gross-column heading can disambiguate a totals row.
                gross=[a for a in all_anchors if a['page']==anchor['page'] and a['box'][1]<row['box'][1] and row['box'][1]-a['box'][1]<240 and re.search(r'brutto|gross',a['label'],re.I)]
                if gross:
                    header=min(gross,key=lambda a:row['box'][1]-a['box'][1])
                    cx=(header['box'][0]+header['box'][2])/2
                    distances=sorted((abs((v['box'][0]+v['box'][2])/2-cx),j) for j,v in enumerate(right))
                    if len(distances)==1 or distances[1][0]-distances[0][0]>12:
                        right=[right[distances[0][1]]]
                # Without a heading keep competing printed values, never guess largest.
            for value in right:add(anchor,row,value,'right')
            continue
        # A column header may have a translation / currency line below it.
        # Stop at the next unrelated field in that column, never traverse item tables.
        if kind=='amount' and (neighbors or re.search(r'\b(?:netto|ohne)\b',tail,re.I)):continue
        if kind=='amount' and re.sub(r'\b(?:EUR|EURO)\b|[\W_]', '', row['text'][:anchor['start']]+tail, flags=re.I):continue
        next_x=min((a['box'][0] for a in neighbors),default=10000)
        left=anchor['box'][0]-8;right_x=next_x-3
        if not positioned:
            left=-1;right_x=10000
        for ri in range(anchor['row']+1,min(len(rows),anchor['row']+5)):
            below=rows[ri]
            if below['page']!=row['page'] or below['box'][1]-row['box'][3]>38:break
            competing=[a for a in all_anchors if a['row']==ri and left<=a['box'][0]<right_x]
            if any(a['role'].split('_')[0]!=kind and a['role']!='other_date' for a in competing):break
            if any(a['role']=='other_date' and not (re.search(r'lieferdatum',a['label'],re.I) and below['text'].lstrip().startswith('/')) for a in competing):break
            candidates=[v for v in values(below,kind) if left<=(v['box'][0]+v['box'][2])/2<right_x]
            # Fields below a stand-alone heading are too weak without column structure.
            if anchor['role']=='number_generic' and not neighbors:break
            if candidates:
                for value in candidates:add(anchor,below,value,'below')
                break
    # Unlabelled place/date line: a review proposal, never override labelled dates.
    if not result['date']:
        for row in rows:
            if re.search(r'^\s*[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß .-]{1,40},\s*(?:den\s+)?\d',row['text']):
                for value in values(row,'date'):
                    add(dict(role='date',label='Orts-/Datumsangabe',score=40,box=row['box']),row,value,'context',reason='Datum ohne ausdrückliche Rechnungsdatum-Beschriftung; bitte prüfen')
    # Corroborate prepaid totals only when two printed net/tax values add up.
    net=[];tax=[]
    for a in all_anchors:
        if a['role'] not in ('net','tax'):continue
        row=rows[a['row']]
        vals=[v for v in values(row,'amount') if v['start']>=a['end']]
        if not vals:
            for below in rows[a['row']+1:a['row']+3]:
                if below['page']!=a['page'] or below['box'][1]-row['box'][3]>30:break
                vals=[v for v in values(below,'amount') if abs((v['box'][0]+v['box'][2])/2-(a['box'][0]+a['box'][2])/2)<45]
                if vals:break
        (net if a['role']=='net' else tax).extend((v['value'],a['page'],row['box'][1]) for v in vals)
    dec=lambda v:Decimal(v.replace(',','.'))
    for hit in result['amount']:
        if any(abs(dec(n)+dec(t)-dec(hit['value']))<=Decimal('.01') for n,np,ny in net for t,tp,ty in tax if np==tp==(hit['page'] or 1) and abs(ny-ty)<100 and abs((hit['box'] or [0,ny])[1]-ny)<130):
            hit['arithmetic']=True;hit['reason']+='; durch gedruckte Netto-/Steuerbeträge rechnerisch gestützt'
            if hit['role']=='amount_prepaid':hit['score']=70
    result['amount']=[h for h in result['amount'] if h['role']!='amount_prepaid' or h.get('arithmetic')]
    return result


def recognize(document,custom=None):
    evidence=gather(document,custom or {});candidates={};status={};selected={}
    for field,hits in evidence.items():
        unique=[];seen=set()
        for h in sorted(hits,key=lambda h:-h['score']):
            key=(h['value'],h['page'],tuple(h['box'] or []),h['label'])
            if key not in seen:unique.append(h);seen.add(key)
        evidence[field]=unique
        best=max((h['score'] for h in unique),default=0)
        # Equally strong semantic evidence remains open, independent of order/count.
        top=[h for h in unique if h['score']>=best-5]
        candidates[field]=list(dict.fromkeys(h['value'] for h in top))
        selected[field]=candidates[field][0] if len(candidates[field])==1 else ''
        status[field]='missing' if not top else 'ambiguous' if len(candidates[field])>1 else 'review' if best<85 or any(h['origin']=='ocr' for h in top) else 'clear'
        for h in unique:h['selected']=bool(selected[field] and h['value']==selected[field] and h['score']>=best-5)
    return dict(values=selected,candidates=candidates,field_evidence=evidence,field_status=status)


def assignment_signature(document,hit):
    """Remember a structural source, never an invoice's concrete value."""
    if not document or not document.get('positioned') or not hit.get('label_box') or not hit.get('box') or hit.get('origin')!='pdf':
        return None
    page=next((p for p in document['pages'] if p['number']==hit['page']),None)
    if not page:return None
    label=hit['label_box'];value=hit['box']
    return dict(version=1,label=re.sub(r'\W','',hit['label'].casefold()),role=hit['role'],relation=hit['relation'],page=hit['page'],
                position=[round(label[0]/page['width'],4),round(label[1]/page['height'],4),round(value[0]/page['width'],4),round(value[1]/page['height'],4)],
                arithmetic=bool(hit.get('arithmetic')))


def same_assignment(saved,current):
    if not current or saved.get('version')!=1:return False
    if any(saved.get(k)!=current.get(k) for k in ('label','role','relation','page','arithmetic')):return False
    old=saved.get('position',[]);new=current['position']
    return len(old)==4 and all(abs(a-b)<=.018 for a,b in zip(old,new))


def apply_assignments(recognized,document,memory):
    for field,entries in memory.items():
        if recognized['field_status'].get(field)!='review':continue
        hits=recognized['field_evidence'][field]
        # Any competing printed value or OCR source keeps manual review necessary.
        if len({h['value'] for h in hits})!=1 or any(h['origin']=='ocr' for h in hits):continue
        selected=[h for h in hits if h['selected']]
        if any(same_assignment(entry,assignment_signature(document,hit)) for entry in entries for hit in selected):
            recognized['field_status'][field]='learned'
            for hit in selected:hit['reason']+='; entspricht einer ausdrücklich gemerkten Feldzuordnung'
