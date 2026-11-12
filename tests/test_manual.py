import unittest, tempfile, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app

class ManualTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.old,self.local=app.DATABASE,app.LOCAL
        app.LOCAL=self.root/'local.json';app.DATABASE=None;app.MANUALS.clear()
        app.new_year({'path':str(self.root/'2026.belegdb'),'year':2026})
        self.fields=dict(provider='Lieferant',date='2026-11-12',number='RE123',amount='1646,23',note='Splitbuchung\n2 Positionen')
    def tearDown(self):
        app.DATABASE,self.old=self.old,None;app.LOCAL=self.local;self.tmp.cleanup()
    def save(self,**fields):
        return app.manual_save(self.fields|{'id':app.manual_preview()['id']}|fields)
    def test_optional_pdf_counter_and_retry(self):
        preview=app.manual_preview();self.assertEqual(app.settings()['counters'],{})
        p=self.fields|{'id':preview['id']}
        self.assertEqual(app.manual_save(p),{'internal':'VTUER26001'})
        self.assertEqual(app.manual_save(p),{'internal':'VTUER26001'})
        row=app.history()[0];self.assertTrue(row['manual']);self.assertEqual(row['destination'],'');self.assertEqual(row['export'],'')
        self.assertEqual(row['amount'],'1.646,23');self.assertEqual(row['note'],self.fields['note'])
        self.assertEqual(app.manual_preview()['internal'],'VTUER26002')
        self.assertEqual(list(self.root.glob('*.tsv')),[])
    def test_link_preserved_and_duplicate_rejected(self):
        path=self.root/'selbst_benannt.pdf';path.write_bytes(b'%PDF test')
        self.save(pdf=str(path));self.assertEqual(path.read_bytes(),b'%PDF test')
        self.assertEqual(app.history()[0]['destination'],str(path))
        with self.assertRaisesRegex(ValueError,'bereits'):self.save(number='OTHER',pdf=str(path))
        with self.assertRaisesRegex(ValueError,'bereits'):self.save()
        self.assertEqual(app.settings()['counters']['2026'],1)
    def test_validation_does_not_consume_number(self):
        for fields in ({'date':'2025-11-12'},{'amount':'1,2'},{'provider':''},{'pdf':str(self.root/'missing.pdf')}):
            with self.assertRaises(ValueError):self.save(**fields)
        self.assertEqual(app.settings()['counters'],{})
        self.save(date='2025-11-12',year_confirmed=True)
    def test_stale_preview_and_year_switch(self):
        preview=app.manual_preview();self.save()
        with self.assertRaisesRegex(ValueError,'Nummernstand'):app.manual_save(self.fields|dict(id=preview['id'],number='OTHER'))
        app.new_year({'path':str(self.root/'2027.belegdb'),'year':2027})
        with self.assertRaisesRegex(ValueError,'abgelaufen'):app.manual_save(self.fields|dict(id=preview['id']))
    def test_normal_export_continues_and_stale_export_fails(self):
        source=self.root/'import.pdf';source.write_bytes(b'%PDF import')
        app.SCANS['test']={'path':source,'hash':app.digest(source)}
        app.save_account({'number':'4910','description':'Porto'})
        payload=dict(settings=app.settings()|{'target':str(self.root/'archive')},rows=[dict(id='test',provider='Post',date='2026-11-12',number='POST1',amount='1646,23',account='4910',bank='1200',reviewed=True)])
        stale=app.make_plan(payload);self.save()
        with self.assertRaisesRegex(ValueError,'Nummernstand'):app.execute(stale['id'])
        plan=app.make_plan(payload);self.assertIn('VTUER26002',plan['tsv']);self.assertIn('1.646,23 €',plan['tsv'])
        app.execute(plan['id']);self.assertEqual(app.manual_preview()['internal'],'VTUER26003')
    def test_amount_format(self):
        from decimal import Decimal
        for raw,want in [('0','0,00'),('-1234567.89','-1.234.567,89'),('12.5','12,50')]:self.assertEqual(app.format_amount(Decimal(raw)),want)

if __name__=='__main__':unittest.main()
