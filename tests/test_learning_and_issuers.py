# SPDX-License-Identifier: GPL-3.0-only
"""Regressions for confirmed generic failures and explicit user-controlled learning."""
import unittest
from identifiers import company_names,find_identifiers
from party_engine import analyze
from recognition import extract_fields
from field_engine import recognize,assignment_signature,apply_assignments
from test_document_engine import document
import test_identifiers as fixtures
import app

class IssuerAndPaymentTests(unittest.TestCase):
    def test_dotted_legal_names_and_foreign_identifier_boundaries(self):
        for ending in ['B.V.','S.A.','GmbH','AG']:
            for suffix in ['', ' Beispielstraße 2']:
                self.assertEqual(company_names('Testfirma '+ending+suffix),['Testfirma '+ending])
        self.assertEqual(company_names('Testfirma AGB'),[])
        for raw in ['NL123456789B01','NL 123 456 789 B01']:
            for tail in ['', ' - Handelsregisternummer 12345678', ' Telefon 1234567']:
                ids=find_identifiers('VAT: '+raw+tail)
                self.assertEqual([i['key'] for i in ids],['NL123456789B01'])
        self.assertEqual(find_identifiers('VAT: ungültig - Register 12345678'),[])

    def test_column_boundaries_and_split_identifiers(self):
        for token in ['DE123456789','DE 123456789']:
            d=document((30,30,'Abrechnungsstelle:'),(250,30,'USt-ID'),(30,45,'Fremde AG'),(250,45,token),(30,60,'VAT DE987654321'))
            ids=analyze('\n'.join(r['text'] for r in d['rows']),d)['identifiers']
            seller=next(i for i in ids if i['value']=='DE123456789');billing=next(i for i in ids if i['value']=='DE987654321')
            self.assertTrue(seller['issuer_usable']);self.assertEqual(seller['locations'][0]['box'][0],250)
            self.assertFalse(billing['issuer_usable']);self.assertIn('billing',billing['roles'])

    def test_collective_opt_in_own_exclusions_and_multiple_rules(self):
        d=document((30,30,'Verkauft von Verkäufer Eins'),(30,110,'Umsatzsteuer erklärt durch Plattform'),(30,125,'VAT LU20260743'))
        text='\n'.join(r['text'] for r in d['rows'])
        rules={'Sammelkonto':{'vat_ids':['LU20260743'],'collective':True}}
        self.assertEqual(extract_fields(text,rules,document=d)['provider'],'Sammelkonto')
        self.assertEqual(extract_fields(text,rules,document=d,own_vat=['LU20260743'])['provider'],'')
        rules['Sammelkonto']['collective']=False
        self.assertEqual(extract_fields(text,rules,document=d)['provider'],'')
        rules['Sammelkonto']['collective']=True;rules['Andere Sammlung']=dict(rules['Sammelkonto'])
        self.assertEqual(extract_fields(text,rules,document=d)['provider'],'')
        self.assertEqual(extract_fields('Ihre VAT LU20260743',rules)['provider'],'')

    def test_paid_total_requires_sum_and_yields_to_invoice_total(self):
        prefix='Warenwert 111,00\nUmsatzsteuer 21,09\n'
        for label in ['Mit Kreditkarte bezahlt','Paid by credit card']:
            r=extract_fields(prefix+label+' 132,09',{})
            self.assertEqual(r['amount'],'132,09');self.assertEqual(r['field_status']['amount'],'review')
            for amount in ['20,00','150,00']:
                self.assertEqual(extract_fields(prefix+label+' '+amount,{})['amount'],'')
            self.assertEqual(extract_fields(label+' 132,09',{})['amount'],'')
            self.assertEqual(extract_fields(prefix+'Rechnungsbetrag 132,09\n'+label+' 150,00',{})['amount'],'132,09')
        d=document((30,30,'Warenwert 111,00'),(30,45,'Umsatzsteuer 21,09'),(30,400,'Paid by credit card 132,09'))
        self.assertEqual(recognize(d)['values']['amount'],'')

class LearningTests(unittest.TestCase):
    def test_changed_values_match_structure_but_conflicts_layout_and_ocr_do_not(self):
        first=document((30,30,'Betrag 12,34'));r=recognize(first)
        signature=assignment_signature(first,r['field_evidence']['amount'][0]);memory={'amount':[signature]}
        second=document((30,30,'Betrag 99,12'));r=recognize(second);apply_assignments(r,second,memory)
        self.assertEqual(r['field_status']['amount'],'learned');self.assertNotIn('value',signature)
        for d in [document((30,30,'Betrag 12,34'),(30,60,'Betrag 11,00')),document((30,100,'Betrag 12,34')),document((30,30,'Total 12,34')),document((30,30,'Betrag'),(30,45,'12,34'))]:
            r=recognize(d);apply_assignments(r,d,memory);self.assertNotEqual(r['field_status']['amount'],'learned')
        for row in second['rows']:
            for word in row['words']:word['origin']='ocr'
        r=recognize(second);apply_assignments(r,second,memory);self.assertEqual(r['field_status']['amount'],'review')

# Reuse fixture setup, not the inherited test cases.
class WorkflowTests(unittest.TestCase):
    setUp=fixtures.DiscoveryTests.setUp
    tearDown=fixtures.DiscoveryTests.tearDown

    def test_suggestions_are_read_only_and_saved_ids_and_memory_persist(self):
        row=app.scan(str(self.root))[0];p=app.provider_suggestions({'id':row['id']})
        self.assertEqual(p['candidates'][0]['name'],'Versand GmbH');self.assertEqual(app.settings()['rules'],{})
        app.save_rule(dict(p['candidates'][0],collective=True))
        response=app.remember_field({'id':row['id'],'provider':'Versand GmbH','field':'amount','index':0})
        self.assertTrue(response['settings']['rules']['Versand GmbH']['field_memory']['amount'])
        app.save_rule({'name':'Versand GmbH','aliases':['Versand GmbH']})
        rule=app.settings()['rules']['Versand GmbH'];self.assertTrue(rule['collective']);self.assertTrue(rule['field_memory'])
        copied=app.new_year({'path':str(self.root/'2027.belegdb'),'year':2027,'template':str(self.year)})
        self.assertEqual(copied['rules']['Versand GmbH']['field_memory'],rule['field_memory'])
        row=app.scan(str(self.root))[0]
        response=app.remember_field({'id':row['id'],'provider':'Versand GmbH','field':'amount','forget':True})
        self.assertNotIn('amount',response['settings']['rules']['Versand GmbH']['field_memory'])
        app.SCANS[row['id']]['path'].write_bytes(b'changed')
        for fn in [app.provider_suggestions,app.page_text]:
            with self.assertRaisesRegex(ValueError,'verändert'):fn({'id':row['id']})
