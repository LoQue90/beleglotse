# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Lorenz Uhlig
import sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app

class YearTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.old,self.local=app.DATABASE,app.LOCAL;app.LOCAL=self.root/'local.json';app.DATABASE=None
        self.year=self.root/'2026.belegdb';app.new_year({'path':str(self.year),'year':2026})
        app.save_account({'number':'4910','description':'Testkonto'})
        self.input=self.root/'Eingang';self.input.mkdir()
        self.s=app.settings()|{'input':str(self.input),'target':str(self.input/'verbucht')}
        app.save_settings(self.s)
    def tearDown(self):
        app.DATABASE=self.old;app.LOCAL=self.local;app.SCANS.clear();app.PLANS.clear();self.temp.cleanup()
    def row(self,number='ABC',date='2026-02-03'):
        p=self.input/(number+'.pdf');p.write_bytes(number.encode())
        app.SCANS[number]={'path':p,'hash':app.digest(p)}
        return dict(id=number,provider='DHL',date=date,number=number,amount='6,19',account='4910',bank='1200',currency='EUR',reviewed=True)
    def plan(self,rows):return app.make_plan({'settings':self.s,'rows':rows})
    def test_new_year_copies_only_master_and_settings(self):
        app.save_account({'number':'1234','description':'Eigenes Konto'})
        app.save_rule({'name':'Firma','account':'1234','bank':'1200','aliases':['Firma GmbH'],'labels':{'amount':'Gesamtsumme\nBetrag'}})
        app.execute(self.plan([self.row()])['id']);before=app.digest(self.year)
        p=self.root/'2027.belegdb';s=app.new_year({'path':str(p),'year':2027,'template':str(self.year)})
        self.assertEqual(app.digest(self.year),before);self.assertEqual(app.history(),[]);self.assertEqual(s['counters'],{})
        self.assertEqual(s['rules']['Firma']['labels']['amount'],['Gesamtsumme','Betrag'])
        self.assertEqual((s['rules']['Firma']['account'],s['rules']['Firma']['bank'],s['rules']['Firma']['aliases']),('1234','1200',['Firma GmbH']))
        self.assertIn({'number':'1234','description':'Eigenes Konto'},s['accounts'])
        self.assertEqual((s['input'],s['target']),('',''))
        app.open_year({'path':str(self.year)});self.assertEqual(len(app.history()),1);self.assertEqual(app.settings()['target'],str(self.input/'verbucht'))
    def test_continue_sequence_when_reset_disabled(self):
        self.s['annual_reset']=False;app.execute(self.plan([self.row()])['id'])
        s=app.new_year({'path':str(self.root/'2027.belegdb'),'year':2027,'template':str(self.year)})
        self.assertEqual(s['counters'],{'2027':1})
        self.s=s|{'target':str(self.input/'verbucht')}
        p=self.plan([self.row('XYZ','2027-01-01')]);self.assertIn('VTUER27002',p['tsv'])
    def test_existing_year_is_never_overwritten(self):
        h=app.digest(self.year)
        with self.assertRaisesRegex(ValueError,'existiert'):app.new_year({'path':str(self.year),'year':2026})
        self.assertEqual(h,app.digest(self.year))
    def test_sorted_numbering_and_preview_does_not_consume(self):
        rows=[self.row('LATE','2026-03-03'),self.row('EARLY','2026-01-01')]
        self.plan(rows);p=self.plan(rows)
        self.assertEqual([x['metadata']['number'] for x in p['items']],['EARLY','LATE'])
        self.assertEqual([x['metadata']['internal'] for x in p['items']],['VTUER26001','VTUER26002'])
        self.assertEqual(app.settings()['counters'],{})
    def test_configurable_filename_and_original_tsv(self):
        self.s.update(prefix='ER-',year_digits=4,sequence_digits=4,filename_pattern='{datum}_{aussteller}_{rechnungsnummer}',number_source='original')
        p=self.plan([self.row()]);i=p['items'][0]
        self.assertEqual(i['metadata']['internal'],'ER-20260001')
        self.assertTrue(i['destination'].endswith('2026-02-03_DHL_ABC.pdf'));self.assertIn('\tABC\tDHL\t',p['tsv'])
    def test_mismatched_year_requires_confirmation(self):
        r=self.row(date='2025-12-31')
        with self.assertRaisesRegex(ValueError,'Buchungsjahr'):self.plan([r])
        r['year_confirmed']=True;p=self.plan([r]);self.assertIn('VTUER26001',p['tsv'])
    def test_switch_invalidates_pending_preview(self):
        p=self.plan([self.row()])
        app.new_year({'path':str(self.root/'2027.belegdb'),'year':2027})
        with self.assertRaisesRegex(ValueError,'abgelaufen'):app.execute(p['id'])
    def test_concurrent_counter_change_blocks(self):
        p=self.plan([self.row()])
        with app.db() as c:c.execute('INSERT INTO counters VALUES (2026,9)')
        with self.assertRaisesRegex(ValueError,'Nummernstand'):app.execute(p['id'])
    def test_default_target_created_at_export_and_no_recursive_import(self):
        from pypdf import PdfWriter
        p=self.input/'one.pdf';writer=PdfWriter();writer.add_blank_page(width=50,height=50);writer.write(p)
        self.s['ocr']=False;app.save_settings(self.s)
        rows=app.scan(str(self.input));r=rows[0]|dict(provider='DHL',date='2026-01-01',number='A',amount='1,00',account='4910',bank='1200',reviewed=True)
        plan=self.plan([r]);self.assertFalse((self.input/'verbucht').exists())
        app.execute(plan['id']);self.assertEqual(len(list((self.input/'verbucht').glob('*.pdf'))),1)
        self.assertEqual(app.scan(str(self.input)),[])
    def test_missing_original_in_filename_is_rejected(self):
        r=self.row();r['number']='';self.s['filename_pattern']='{rechnungsnummer}.pdf'
        with self.assertRaisesRegex(ValueError,'Original'):self.plan([r])
    def test_unknown_placeholder_and_path_rejected(self):
        r=self.row()
        for pattern in ['{unknown}.pdf','../{belegnummer}.pdf','{aussteller.__class__}.pdf']:
            self.s['filename_pattern']=pattern
            with self.assertRaises(ValueError):self.plan([r])

if __name__=='__main__':unittest.main()
