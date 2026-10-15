# SPDX-License-Identifier: GPL-3.0-only
"""Positioned, UI-independent document model. Coordinates are PDF points, top-left."""
import re
from statistics import median

VERSION = 1


def rectangle(items):
    boxes = [x['box'] for x in items]
    return [min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes)]


def make_rows(words, page):
    rows = []
    for word in sorted(words, key=lambda w: ((w['box'][1]+w['box'][3])/2, w['box'][0])):
        box = word['box']; center = (box[1]+box[3])/2
        candidates = [r for r in rows[-8:] if abs(r['center']-center) <= max(2.2, min(r['height'],box[3]-box[1])*.42)]
        if candidates:
            row = min(candidates, key=lambda r: abs(r['center']-center));row['words'].append(word)
            row['center'] = median((w['box'][1]+w['box'][3])/2 for w in row['words'])
        else:
            rows.append(dict(words=[word],center=center,height=box[3]-box[1]))
    result = []
    for row in sorted(rows, key=lambda r:r['center']):
        parts=[]; ordered=sorted(row['words'],key=lambda w:w['box'][0]);pos=0
        for word in ordered:
            word['start']=pos;word['end']=pos+len(word['text']);pos=word['end']+1;parts.append(word['text'])
        result.append(dict(text=' '.join(parts),words=ordered,box=rectangle(ordered),page=page))
    return result


def read_geometry(path):
    import pypdfium2 as pdfium
    result=dict(version=VERSION,pages=[],rows=[],positioned=True)
    with pdfium.PdfDocument(str(path),password='') as pdf:
        for page_no in range(len(pdf)):
            page=pdf[page_no]
            try:
                width,height=page.get_size();words=[];chars=[]
                def flush():
                    if chars:
                        words.append(dict(text=''.join(c['text'] for c in chars),box=rectangle(chars),origin='pdf'))
                        chars.clear()
                textpage=page.get_textpage()
                try:
                    for i in range(textpage.count_chars()):
                        char=textpage.get_text_range(i,1)
                        if not char or char.isspace() or char=='\x00':flush();continue
                        left,bottom,right,top=textpage.get_charbox(i)
                        box=[left,height-top,right,height-bottom]
                        if chars:
                            prev=chars[-1]['box'];h=max(box[3]-box[1],prev[3]-prev[1],1)
                            if box[0]-prev[2]>h*.48 or box[0]<prev[0]-h or abs(box[3]-prev[3])>h*.6:flush()
                        chars.append(dict(text=char,box=box))
                    flush()
                finally:textpage.close()
                rows=make_rows(words,page_no+1)
                result['pages'].append(dict(number=page_no+1,width=width,height=height))
                result['rows'].extend(rows)
            finally:page.close()
    return result


def text_document(text):
    """Fallback for OCR/plain text and API clients without positional input."""
    rows=[]
    for y,line in enumerate(text.splitlines()):
        words=[dict(text=m.group(),box=[m.start()*5,y*14,m.end()*5,y*14+10],origin='text') for m in re.finditer(r'\S+',line)]
        if words:rows.extend(make_rows(words,1))
    return dict(version=VERSION,pages=[],rows=rows,positioned=False)


def span_box(row,start,end):
    words=[w for w in row['words'] if w['end']>start and w['start']<end]
    return rectangle(words) if words else row['box']
