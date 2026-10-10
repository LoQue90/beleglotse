# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Lorenz Uhlig
import unittest, tempfile, sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.old=app.DATABASE; self.oldlocal=app.LOCAL; app.LOCAL=self.root/'local.json'; app.DATABASE=None; app.new_year({'path':str(self.root/'2026.belegdb'),'year':2026}); app.SCANS.clear(); app.PLANS.clear()
        app.save_account({'number':'4910','description':'Testkonto'})
        self.source=self.root/'original.pdf'; self.source.write_bytes(b'%PDF-test-content')
        self.target=self.root/'archive'; self.target.mkdir()
        app.SCANS['one']={'path':self.source,'hash':app.digest(self.source)}
        self.settings=app.settings(); self.settings['target']=str(self.target)
        self.row=dict(id='one',provider='DHL',date='2026-01-28',number='E002F95968',amount='6,19',account='4910',bank='1200',description='DHL',reviewed=True,currency='EUR')
    def tearDown(self):
        app.DATABASE=self.old; app.LOCAL=self.oldlocal; self.tmp.cleanup()
    def plan(self): return app.make_plan({'settings':self.settings,'rows':[self.row]})
    def test_exact_tsv_and_move_and_duplicate(self):
        p=self.plan()
        self.assertEqual(p['tsv'],'Ausgabe\t28.01.2026\tVTUER26001\tDHL\t6,19 €\tNULL\t4910\t1200\r\n')
        self.assertTrue(self.source.exists())
        r=app.execute(p['id']); self.assertFalse(self.source.exists())
        self.assertEqual(Path(p['items'][0]['destination']).read_bytes(),b'%PDF-test-content')
        self.assertEqual(Path(r['export']).read_bytes(),p['tsv'].encode())
        self.source.write_bytes(b'%PDF-test-content')
        with self.assertRaisesRegex(ValueError,'bereits exportierte'): self.plan()
    def test_collision_never_overwrites(self):
        p=self.plan(); dest=Path(p['items'][0]['destination']); dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b'existing')
        with self.assertRaises(FileExistsError): app.execute(p['id'])
        self.assertEqual(dest.read_bytes(),b'existing');self.assertTrue(self.source.exists())
    def test_changed_source_does_not_move(self):
        p=self.plan();self.source.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'verändert'):app.execute(p['id'])
        self.assertTrue(self.source.exists());self.assertFalse(Path(p['export']).exists())
    def test_missing_account_and_tab_rejected(self):
        self.row['account']=''
        with self.assertRaises(ValueError):self.plan()
        self.row['account']='4910';self.row['provider']='bad\tfield'
        with self.assertRaises(ValueError):self.plan()
    def test_signed_amounts(self):
        self.row['amount']='-1.234,56';self.assertIn('-1234,56 €',self.plan()['tsv'])
        self.row['amount']='0,00';self.assertIn('0,00 €',self.plan()['tsv'])
    def test_write_failure_rolls_back_copies(self):
        p=self.plan()
        original=Path.open
        def fail(path,*args,**kwargs):
            if str(path)==p['export']:raise OSError('disk full')
            return original(path,*args,**kwargs)
        with patch.object(Path,'open',fail):
            with self.assertRaises(OSError):app.execute(p['id'])
        self.assertTrue(self.source.exists());self.assertFalse(Path(p['items'][0]['destination']).exists())
        with app.db() as c:self.assertEqual(c.execute('SELECT count(*) FROM processed').fetchone()[0],0)
    def test_delete_failure_retains_original_and_ledger(self):
        p=self.plan(); original=Path.unlink
        def fail(path,*args,**kwargs):
            if path==self.source:raise PermissionError('locked')
            return original(path,*args,**kwargs)
        with patch.object(Path,'unlink',fail):r=app.execute(p['id'])
        self.assertEqual(len(r['warnings']),1);self.assertTrue(self.source.exists());self.assertTrue(Path(r['export']).exists())
        with self.assertRaises(ValueError):self.plan()

if __name__=='__main__':unittest.main()
