# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Lorenz Uhlig
import sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
from identifiers import find_identifiers, vat, tax, layout_candidates
from recognition import extract_fields
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

def invoice(path):
    writer=PdfWriter();page=writer.add_blank_page(width=600,height=800)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    stream=DecodedStreamObject();stream.set_data(b'BT /F1 10 Tf 30 750 Td (Versand GmbH) Tj 0 -25 Td (Rechnungsdatum: 01.02.2026) Tj 0 -25 Td (Rechnungsnummer: TEST-1) Tj 0 -25 Td (Gesamtbetrag: 17,00) Tj ET BT /F1 10 Tf 30 200 Td (Versand GmbH) Tj 0 -20 Td (USt-ID: DE123456789) Tj 0 -20 Td (Steuernummer: 123/456/78901) Tj ET BT /F1 10 Tf 320 200 Td (Andere AG) Tj ET')
    page[NameObject('/Contents')]=writer._add_object(stream);writer.write(path)

class IdentifierTests(unittest.TestCase):
    def test_normalization_and_own_exclusion(self):
        self.assertEqual(vat('de 123 456 789'),'DE123456789')
        self.assertEqual(tax('de:123/456/78901'),'DE:12345678901')
        ids=find_identifiers('USt-ID: DE 123 456 789\nSt.Nr. 123/456/78901',own_vat=['DE123456789'],own_tax=['DE:12345678901'])
        self.assertEqual(len(ids),2);self.assertTrue(all(i['own'] for i in ids))
        with self.assertRaises(ValueError):vat('DE123')
        with self.assertRaises(ValueError):tax('123/456/78901')

    def test_identity_priority_over_overlapping_names(self):
        rules={'Transport':{'vat_ids':['DE123456789']},'Abrechnung':{'aliases':['Andere AG']}}
        r=extract_fields('Andere AG\nUSt-ID: DE123456789',rules)
        self.assertEqual(r['provider'],'Transport');self.assertIn('bestätigte Kennung',r['note'])

    def test_conflicting_identities_never_use_keyword_tiebreak(self):
        rules={'A':{'aliases':['A GmbH'],'vat_ids':['DE123456789']},'B':{'vat_ids':['DE987654321']}}
        self.assertEqual(extract_fields('A GmbH\nDE123456789\nDE987654321',rules)['provider'],'')

    def test_own_and_recipient_ids_do_not_match(self):
        rules={'A':{'vat_ids':['DE123456789']}}
        self.assertEqual(extract_fields('DE123456789',rules,own_vat=['DE123456789'])['provider'],'')
        self.assertEqual(extract_fields('Ihre USt-ID: DE123456789',rules)['provider'],'')

    def test_tax_needs_country_and_country_matches(self):
        rules={'A':{'tax_ids':['DE:12345678901']}}
        text='Steuernummer: 123/456/78901'
        self.assertEqual(extract_fields(text,rules)['provider'],'')
        self.assertEqual(extract_fields(text,rules,tax_country='AT')['provider'],'')
        self.assertEqual(extract_fields(text,rules,tax_country='DE')['provider'],'A')

    def test_layout_prefers_same_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'invoice.pdf';invoice(p)
            result=layout_candidates(p,find_identifiers('DE123456789'))
            self.assertEqual(result[('vat','DE123456789')]['names'][0],'Versand GmbH')
            self.assertEqual(result[('vat','DE123456789')]['page'],1)

class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.old=(app.DATABASE,app.LOCAL)
        app.DATABASE=None;app.LOCAL=self.root/'local.json';self.year=self.root/'2026.belegdb'
        app.new_year({'path':str(self.year),'year':2026});invoice(self.root/'one.pdf');invoice(self.root/'two.pdf')

    def tearDown(self):
        app.DATABASE,app.LOCAL=self.old;app.SCANS.clear();app.PLANS.clear();app.DISCOVERIES.clear();self.temp.cleanup()

    def test_scan_confirm_merge_and_rescan(self):
        result=app.discover(str(self.root));self.assertEqual(len(result['groups']),1)
        self.assertEqual(app.settings()['rules'],{})
        g=next(g for g in result['groups'] if g['kind']=='vat');self.assertEqual(len({f['id'] for f in g['files']}),2);self.assertEqual(len(g['identifiers']),2)
        self.assertEqual(g['name'],'Versand GmbH')
        with self.assertRaises(ValueError):app.confirm_discovery({'id':g['id'],'name':'Versand'})
        app.confirm_discovery({'id':g['id'],'name':'Versand','confirmed':True})
        rule=app.settings()['rules']['Versand'];self.assertEqual(rule['aliases'],[])
        self.assertEqual(rule['vat_ids'],['DE123456789']);self.assertEqual(rule['tax_ids'],['DE:12345678901'])
        self.assertEqual([r['provider'] for r in app.scan(str(self.root))],['Versand','Versand'])
        with self.assertRaises(ValueError):app.confirm_discovery({'id':g['id'],'name':'Other','confirmed':True})

    def test_own_ids_blocked_shared_ids_require_name(self):
        s=app.settings();s['own_vat']=['DE123456789'];s['own_tax']=['DE:12345678901'];app.save_settings(s)
        result=app.discover(str(self.root));self.assertTrue(result['groups']);self.assertTrue(all(g['kind']=='name' for g in result['groups']))
        self.assertTrue(all(not c['vat_ids'] and not c['tax_ids'] for row in app.SCANS for c in app.provider_suggestions({'id':row})['candidates']))
        with self.assertRaisesRegex(ValueError,'Eigene'):app.save_rule({'name':'Own','vat_ids':['DE123456789']})
        app.save_rule({'name':'A','vat_ids':['DE987654321']})
        app.save_rule({'name':'B','vat_ids':['DE987654321']})
        self.assertEqual(extract_fields('DE987654321',app.settings()['rules'])['provider'],'')
        app.save_rule({'name':'B','vat_ids':['DE987654321'],'aliases':['B GmbH']})
        self.assertEqual(extract_fields('B GmbH DE987654321',app.settings()['rules'])['provider'],'B')

    def test_identifiers_survive_edit_and_year_copy(self):
        app.save_rule({'name':'Firma','vat_ids':['DE123456789']})
        app.save_rule({'name':'Firma','aliases':['Firma GmbH']})
        self.assertEqual(app.settings()['rules']['Firma']['vat_ids'],['DE123456789'])
        s=app.new_year({'path':str(self.root/'2027.belegdb'),'year':2027,'template':str(self.year)})
        self.assertEqual(s['rules']['Firma']['vat_ids'],['DE123456789'])

    def test_unreadable_in_discovery_report(self):
        (self.root/'invalid.pdf').write_bytes(b'invalid')
        result=app.discover(str(self.root))
        self.assertTrue(any('PDF konnte nicht gelesen' in row['note'] for row in result['unresolved']))
