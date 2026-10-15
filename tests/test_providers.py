# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Lorenz Uhlig
import sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
from recognition import extract_fields

class ProviderRecognitionTests(unittest.TestCase):
    def test_no_builtin_supplier_or_layout(self):
        for text in ['Deutsche Post AG\nPaket\nGesamtsumme Brutto: 6,19', 'Mollie B.V.\nRechnungsreferenz: A1', 'Lieferant GmbH']:
            self.assertEqual(extract_fields(text,{})['provider'],'')

    def test_exclusion_resolves_overlapping_suppliers(self):
        rules={'Brief':{'aliases':['Deutsche Post'],'exclude':['DHL Paket']},
               'Paket':{'aliases':['DHL Paket','Deutsche Post'],'match_mode':'all'}}
        result=extract_fields('DEUTSCHE POST AG\nDHL\nPaket\nRechnungsbetrag: 9,00',rules)
        self.assertEqual(result['provider'],'Paket')
        self.assertEqual(result['provider_matches'][0]['excluded'],['DHL Paket'])
        self.assertEqual(extract_fields('Deutsche Post AG\nBrief',rules)['provider'],'Brief')

    def test_all_missing_and_word_boundaries(self):
        rules={'A':{'aliases':['Firma','UST123'],'match_mode':'all'}}
        result=extract_fields('Firma',rules)
        self.assertEqual(result['provider'],'')
        self.assertEqual(result['provider_matches'][0]['missing'],['UST123'])
        self.assertEqual(extract_fields('Firmax UST123',rules)['provider'],'')
        self.assertEqual(extract_fields('firma UST123',rules)['provider'],'A')

    def test_legacy_any_and_no_implicit_name(self):
        self.assertEqual(extract_fields('Alternative',{'A':{'aliases':['Firma','Alternative']}})['provider'],'A')
        self.assertEqual(extract_fields('Firma',{'Firma':{'aliases':[]}})['provider'],'')

    def test_no_order_priority_or_field_rules_before_resolution(self):
        rules={'A':{'aliases':['Firma'],'labels':{'amount':['Sonderbetrag']}},'B':{'aliases':['Firma']}}
        for mapping in [rules,dict(reversed(list(rules.items())))]:
            result=extract_fields('Firma\nSonderbetrag: 12,00',mapping)
            self.assertEqual((result['provider'],result['amount']),('',''))
            self.assertIn('Mehrere Rechnungssteller',result['note'])
        self.assertEqual(extract_fields('Firma\nSonderbetrag: 12,00',rules,selected_provider='A')['amount'],'12,00')

class ProviderDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.previous=(app.DATABASE,app.LOCAL)
        app.DATABASE=None;app.LOCAL=self.root/'local.json'
        self.year=self.root/'2026.belegdb'
        app.new_year({'path':str(self.year),'year':2026})

    def tearDown(self):
        app.DATABASE,app.LOCAL=self.previous
        app.SCANS.clear();app.PLANS.clear();self.tmp.cleanup()

    def test_empty_year_and_unassigned_supplier(self):
        self.assertEqual(len(app.settings()['accounts']),341)
        self.assertEqual(app.settings()['rules'],{})
        s=app.save_rule({'name':'Firma','aliases':'Firma AG','exclude':'Andere Firma','match_mode':'all'})
        self.assertEqual((s['rules']['Firma']['account'],s['rules']['Firma']['bank']),('',''))
        self.assertEqual(s['rules']['Firma']['exclude'],['Andere Firma'])
        with self.assertRaises(ValueError):app.save_rule({'name':'Firma','bank':'abc'})
        with self.assertRaises(ValueError):app.save_rule({'name':'Firma','match_mode':'first'})


    def test_create_only_persists_and_never_overwrites_existing_rule(self):
        rule={'name':'Firma','aliases':['Firma AG'],'create_only':True}
        app.save_rule(rule)
        app.open_year({'path':str(self.year)})
        before=app.settings()['rules']['Firma']
        self.assertEqual(before['aliases'],['Firma AG'])
        for name in ['Firma','firma','FIRMA']:
            with self.assertRaisesRegex(ValueError,'existiert bereits'):
                app.save_rule({'name':name,'aliases':[],'create_only':True})
        self.assertEqual(app.settings()['rules'],{'Firma':before})
        app.save_rule({'name':'Firma','aliases':[]})
        self.assertEqual(app.settings()['rules']['Firma']['aliases'],[])

    def test_manual_reprocess_fields_accounts_duplicate_and_plan(self):
        app.save_account({'number':'4321','description':'Eigenes Konto'})
        app.save_rule({'name':'B','account':'4321','bank':'9876','aliases':['B'],
                       'labels':{'date':'Tag','number':'Referenz','amount':'Sonderbetrag'}})
        path=self.root/'invoice.pdf';path.write_bytes(b'test')
        app.SCANS['x']={'path':path,'hash':app.digest(path),'text':'A\nTag: 01.02.2026\nReferenz: NEU\nSonderbetrag: 17,00','read_notes':['OCR verwendet.']}
        app.PLANS['old']={}
        with app.db() as c:c.execute('INSERT INTO processed (hash,invoice_key) VALUES (?,?)',('other-hash','b|neu'))
        r=app.reprocess({'id':'x','provider':'B'})
        self.assertEqual((r['provider'],r['date'],r['number'],r['amount'],r['account'],r['bank']),('B','2026-02-01','NEU','17,00','4321','9876'))
        self.assertTrue(r['duplicate']);self.assertFalse(r['reviewed']);self.assertEqual(app.PLANS,{})
        self.assertIn('OCR verwendet',r['note'])
        r=app.reprocess({'id':'x','provider':'Neuer Anbieter'})
        self.assertEqual((r['amount'],r['account'],r['bank']),('','',''))
        self.assertFalse(r['duplicate'])
        path.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'verändert'):app.reprocess({'id':'x','provider':'B'})

    def test_scan_no_implicit_bank_and_keeps_custom_provider_name(self):
        path=self.root/'invoice.pdf';path.write_bytes(b'test')
        app.save_rule({'name':'Post','aliases':['My supplier']})
        with patch('recognition.pdf_text',return_value=('My supplier\nGesamtbetrag: 10,00',[],[])):
            result=app.scan(str(self.root))[0]
        self.assertEqual((result['provider'],result['bank'],result['account']),('Post','',''))


    def test_layout_survives_scan_and_manual_reprocessing(self):
        path=self.root/'invoice.pdf';path.write_bytes(b'test')
        app.save_rule({'name':'Supplier','aliases':['My supplier']})
        plain='My supplier\nRechnungsnummer:\nRechnungsdatum:\nRechnungsbetrag:\nINV-42\n28/05/2026\n52,69 EUR'
        lines=['Rechnungsnummer: INV-42','Rechnungsdatum: 28/05/2026','Rechnungsbetrag: 52,69 EUR']
        with patch('recognition.pdf_text',return_value=(plain,[],lines)):
            row=app.scan(str(self.root))[0]
        result=app.reprocess({'id':row['id'],'provider':'Supplier'})
        self.assertEqual((row['number'],row['date'],row['amount']),('INV-42','2026-05-28','52,69'))
        self.assertEqual((result['number'],result['date'],result['amount']),('INV-42','2026-05-28','52,69'))
        self.assertNotIn('layout_lines',row)

    def test_unreadable_pdf_can_be_assigned_for_manual_entry(self):
        path=self.root/'invoice.pdf';path.write_bytes(b'invalid')
        row=app.scan(str(self.root))[0]
        result=app.reprocess({'id':row['id'],'provider':'Manuell'})
        self.assertEqual(result['provider'],'Manuell')
        self.assertIn('PDF konnte nicht gelesen werden',result['note'])
