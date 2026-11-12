import unittest, tempfile, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app

class HistoryDeleteTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.old,self.local=app.DATABASE,app.LOCAL;app.LOCAL=self.root/'local.json';app.DATABASE=None
        app.new_year({'path':str(self.root/'2026.belegdb'),'year':2026})
        self.fields=dict(provider='Lieferant',date='2026-11-12',number='RE1',amount='1646,23')
    def tearDown(self):
        app.DATABASE=self.old;app.LOCAL=self.local;self.tmp.cleanup()
    def add(self,**fields):
        app.manual_save(self.fields|dict(id=app.manual_preview()['id'])|fields)
        return app.history()[0]
    def delete(self,row,**fields):
        return app.delete_history(dict(id=row['id'],year_file=str(app.DATABASE.resolve()),confirmed=True)|fields)
    def test_manual_delete_retains_counter_and_allows_reentry(self):
        row=self.add();self.delete(row);self.assertEqual(app.history(),[])
        self.assertEqual(app.manual_preview()['internal'],'VTUER26002')
        row=self.add();self.assertEqual(row['internal'],'VTUER26002')
    def test_export_delete_preserves_files_and_invalidates_previews(self):
        source=self.root/'import.pdf';source.write_bytes(b'%PDF import')
        app.SCANS['test']={'path':source,'hash':app.digest(source)}
        app.save_account({'number':'4910','description':'Porto'})
        payload=dict(settings=app.settings()|{'target':str(self.root/'archive')},rows=[self.fields|dict(id='test',account='4910',bank='1200',reviewed=True)])
        plan=app.make_plan(payload);app.execute(plan['id']);row=app.history()[0]
        pdf,tsv=Path(row['destination']),Path(row['export']);before=pdf.read_bytes(),tsv.read_bytes()
        self.delete(row);self.assertEqual((pdf.read_bytes(),tsv.read_bytes()),before)
        self.assertEqual(app.settings()['counters']['2026'],1);self.assertEqual(app.PLANS,{});self.assertEqual(app.MANUALS,{})
        app.SCANS['test']={'path':pdf,'hash':app.digest(pdf)}
        self.assertEqual(app.make_plan(payload)['items'][0]['metadata']['internal'],'VTUER26002')
    def test_confirmation_year_guard_and_missing_id(self):
        row=self.add()
        for fields in ({'confirmed':False},{'year_file':'different.belegdb'},{'id':'not-present'}):
            with self.assertRaises(ValueError):self.delete(row,**fields)
        self.assertEqual(len(app.history()),1)
        self.delete(row)
        with self.assertRaises(ValueError):self.delete(row)
        self.assertEqual(app.settings()['counters']['2026'],1)

if __name__=='__main__':unittest.main()
