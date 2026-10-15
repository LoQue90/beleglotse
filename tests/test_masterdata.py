# SPDX-License-Identifier: GPL-3.0-only
import tempfile, unittest
from pathlib import Path
import app
from test_identifiers import invoice

class MasterDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.old=app.DATABASE,app.LOCAL
        app.DATABASE=None;app.LOCAL=self.root/'local.json';self.year=self.root/'2026.belegdb'
        app.new_year({'path':str(self.year),'year':2026})
    def tearDown(self):
        app.DATABASE,app.LOCAL=self.old;app.SCANS.clear();app.PLANS.clear();app.DISCOVERIES.clear();self.tmp.cleanup()
    def test_template_import_atomicity_and_year_copy(self):
        s=app.settings();self.assertEqual(len(s['accounts']),341)
        self.assertIn('Sammelposten - selbst gesch.',next(a['description'] for a in s['accounts'] if a['number']=='486'))
        app.save_account({'number':'3200','description':'Eigener Name','disabled':True})
        app.import_accounts({'text':'Nummer;Bezeichnung\n99999;Eigenes Konto\n'})
        with self.assertRaises(ValueError):app.import_accounts({'text':'88888;Darf nicht gespeichert werden\nkaputt'})
        self.assertFalse(any(a['number']=='88888' for a in app.settings()['accounts']))
        app.save_tax_rate({'name':'Eigener Steuersatz'})
        app.save_rule({'name':'Firma','account':'3200','bank':'1200','tax_rate':'Eigener Steuersatz'})
        s=app.new_year({'path':str(self.root/'2027.belegdb'),'year':2027,'template':str(self.year)})
        self.assertIn('3200',s['disabled_accounts']);self.assertEqual(s['rules']['Firma']['tax_rate'],'Eigener Steuersatz')
        self.assertIn('Eigener Steuersatz',s['tax_rates']);self.assertTrue(any(a['number']=='99999' for a in s['accounts']))
        self.assertEqual(next(a['description'] for a in s['accounts'] if a['number']=='3200'),'Eigener Name')
    def test_per_invoice_override_export_and_tax_rename(self):
        invoice(self.root/'one.pdf');app.save_rule({'name':'Versand','vat_ids':['DE123456789'],'account':'3200','bank':'1200'})
        r=app.scan(str(self.root))[0];self.assertEqual(r['tax_rate'],'Keine Vorsteuer')
        r.update(account='4970',bank='1000',tax_rate=app.DEFAULT['tax_rates'][1],reviewed=True)
        s=app.settings();s['target']=str(self.root/'out')
        plan=app.make_plan({'settings':s,'rows':[r]})
        self.assertEqual(plan['tsv'].splitlines()[0].split('\t')[5:],['4970',app.DEFAULT['tax_rates'][1],'1000'])
        self.assertEqual(app.settings()['rules']['Versand']['account'],'3200');self.assertEqual(app.settings()['rules']['Versand']['tax_rate'],'Keine Vorsteuer')
        app.save_tax_rate({'old':'Keine Vorsteuer','name':'Keine Vorsteuer angepasst'})
        self.assertEqual(app.settings()['rules']['Versand']['tax_rate'],'Keine Vorsteuer angepasst');self.assertEqual(app.PLANS,{})
        self.assertEqual(app.reprocess({'id':r['id'],'provider':'Versand'})['tax_rate'],'Keine Vorsteuer angepasst')
    def test_conflicting_preferred_names_not_bundled(self):
        from unittest.mock import patch
        invoice(self.root/'one.pdf')
        geometry={('vat','DE123456789'):{'names':['Firma A'],'page':1},('tax','DE:12345678901'):{'names':['Firma B'],'page':1}}
        with patch.object(app,'layout_candidates',return_value=geometry):result=app.discover(str(self.root))
        self.assertEqual(len(result['groups']),2)
