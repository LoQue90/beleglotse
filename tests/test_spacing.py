import unittest
from document_model import make_rows,reconcile_spacing
from field_engine import recognize

class SpacingTests(unittest.TestCase):
    def rows(self,parts,gap=3,origin='pdf'):
        words=[];x=20
        for text in parts:
            words.append(dict(text=text,box=[x,20,x+len(text)*5,29],origin=origin));x+=len(text)*5+gap
        return make_rows(words,1)

    def test_number_and_date_keep_evidence_boxes(self):
        for parts,plain,field,value in [(['Rechnungs-Nr.:','DOF-261','102ABC-12345'],'Rechnungs-Nr.: DOF-261102ABC-12345','number','DOF-261102ABC-12345'),(['Erstellt','am','02.1','1','.2026'],'Erstellt am 02.11.2026','date','2026-11-02')]:
            rows=self.rows(parts);fixed=reconcile_spacing(rows,plain)
            d=dict(positioned=True,pages=[dict(number=1,width=600,height=800)],rows=fixed)
            result=recognize(d)
            self.assertEqual(result['values'][field],value)
            self.assertEqual(fixed[0]['words'][-1]['box'][2],rows[0]['words'][-1]['box'][2])
            for w in fixed[0]['words']:self.assertEqual(fixed[0]['text'][w['start']:w['end']],w['text'])

    def test_preserve_real_gaps_columns_ocr_and_uncertain_lines(self):
        for parts,plain,gap,origin in [(['AB','123'],'AB 123',3,'pdf'),(['AB','123'],'AB123',60,'pdf'),(['AB','123'],'AB123',3,'ocr'),(['AB','123'],'AB123\nAB 123',3,'pdf'),(['AB','123'],'Other AB123',3,'pdf')]:
            rows=self.rows(parts,gap,origin)
            self.assertEqual(reconcile_spacing(rows,plain)[0]['text'],'AB 123')
