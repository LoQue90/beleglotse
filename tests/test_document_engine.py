# SPDX-License-Identifier: GPL-3.0-only
"""Synthetic structural regressions; no private invoices in the repository."""
import unittest
from document_model import make_rows
from field_engine import recognize, date_value, money_value
from recognition import extract_fields


def document(*lines):
    words=[]
    for x,y,text in lines:
        offset=x
        for token in text.split():
            words.append(dict(text=token,box=[offset,y,offset+len(token)*5,y+9],origin='pdf'))
            offset+=len(token)*5+4
    return dict(positioned=True,pages=[dict(number=1,width=600,height=800)],rows=make_rows(words,1))


class DocumentEngineTests(unittest.TestCase):
    def test_headers_with_values_in_columns_and_translation(self):
        d=document((30,30,'Rechnungsnr.'),(200,30,'Rechnungsdatum'),(400,30,'Seite'),
                   (30,43,'Invoice No.'),(200,43,'Invoice Date'),(400,43,'Page No.'),
                   (30,58,'INV-82'),(200,58,'21-APR-26'),(400,58,'1 of 2'))
        r=recognize(d)
        self.assertEqual(r['values']['number'],'INV-82')
        self.assertEqual(r['values']['date'],'2026-04-21')
        self.assertEqual(r['field_evidence']['number'][0]['page'],1)
        self.assertLess(r['field_evidence']['number'][0]['box'][0],100)

    def test_gross_column_in_total_row(self):
        d=document((30,30,'Material'),(230,30,'Nettobetrag'),(350,30,'Steuer'),(450,30,'Bruttobetrag'),
                   (30,100,'Gesamtbetrag'),(230,100,'80,00'),(350,100,'15,20'),(450,100,'95,20'))
        self.assertEqual(recognize(d)['values']['amount'],'95,20')

    def test_table_without_column_meaning_is_ambiguous(self):
        d=document((30,30,'Gesamtbetrag'),(230,30,'80,00'),(350,30,'15,20'),(450,30,'95,20'))
        r=recognize(d);self.assertEqual(r['values']['amount'],'');self.assertEqual(r['field_status']['amount'],'ambiguous')

    def test_open_balance_not_invoice_total(self):
        r=extract_fields('Gesamtbetrag 42,80\nZahlung 42,80\nOffener Betrag 0,00',{})
        self.assertEqual(r['amount'],'42,80')
        self.assertEqual(extract_fields('Offener Betrag 0,00',{})['amount'],'')

    def test_custom_labels_supplement_defaults_and_normalize_colons(self):
        rules={'A':{'labels':{'number':['Belegnummer:'],'date':['Dokumenttag'],'amount':['Spezialsumme']}}}
        r=extract_fields('Rechnungsnummer\u00a0X-73\nRechnungsdatum 01.02.2026\nGesamtbetrag 17,00',rules,selected_provider='A')
        self.assertEqual((r['number'],r['date'],r['amount']),('X-73','2026-02-01','17,00'))
        self.assertEqual(extract_fields('Belegnummer\u00a0X-73',rules,selected_provider='A')['number'],'X-73')

    def test_misplaced_field_label_cannot_redefine_date_as_number(self):
        r=extract_fields('Rechnungsdatum 01.02.2026',{'A':{'labels':{'number':['Rechnungsdatum']}}},selected_provider='A')
        self.assertEqual(r['number'],'');self.assertEqual(r['date'],'2026-02-01')

    def test_unlabelled_date_is_review_proposal(self):
        r=extract_fields('Bonn, 20.07.2026\nRechnung X-74',{})
        self.assertEqual(r['date'],'2026-07-20');self.assertEqual(r['field_status']['date'],'review')

    def test_missing_invoice_date_does_not_take_separate_delivery_date(self):
        d=document((30,20,'Rechnungsdatum'),(30,34,'Lieferdatum 01.02.2026'))
        self.assertEqual(recognize(d)['values']['date'],'')

    def test_named_months_invalid_dates_and_trailing_minus(self):
        for raw,expected in [('16 März 2026','2026-03-16'),('21-APR-26','2026-04-21'),('Apr 21, 2026','2026-04-21'),('31.02.2026','')]:
            self.assertEqual(date_value(raw),expected)
        self.assertEqual(money_value('1.234,56-'),'-1234,56')

    def test_unit_prices_and_percentages_are_not_totals(self):
        for text in ['Betrag 11.830','Betrag 19,00 %','Betrag am 14.01.2026']:
            self.assertEqual(extract_fields(text,{})['amount'],'')

    def test_ocr_proposal_requires_review(self):
        d=document((30,30,'Rechnungsnummer X-5'))
        for row in d['rows']:
            for word in row['words']:word['origin']='ocr'
        self.assertEqual(recognize(d)['field_status']['number'],'review')

    def test_prepaid_requires_printed_arithmetic_support(self):
        self.assertEqual(extract_fields('Prepaid EUR 23.80',{})['amount'],'')
        r=extract_fields('Nettobetrag 20.00\nUmsatzsteuer 3.80\nPrepaid EUR 23.80',{})
        self.assertEqual(r['amount'],'23,80');self.assertEqual(r['field_status']['amount'],'review')

    def test_conflicting_strong_totals_stay_open_with_arithmetic(self):
        r=extract_fields('Netto 10,00\nMwSt 1,90\nRechnungsbetrag 11,90\nGesamtbetrag 12,90',{})
        self.assertEqual(r['amount'],'');self.assertEqual(r['field_status']['amount'],'ambiguous')

    def test_item_column_is_not_invoice_total(self):
        d=document((30,20,'Artikel'),(250,20,'Gesamtpreis'),(30,40,'Produkt'),(250,40,'25,00'))
        self.assertEqual(recognize(d)['values']['amount'],'')


class PartyTests(unittest.TestCase):
    def test_punctuation_in_confirmed_name_does_not_break_rescan(self):
        r=extract_fields('Verkauft von Example S.a.r.l., Niederlassung Deutschland',{'Example':{'aliases':['Example S.a.r.l. Niederlassung Deutschland']}})
        self.assertEqual(r['provider'],'Example')

    def test_platform_identifier_cannot_identify_seller(self):
        d=document((300,20,'Verkauft von SellerOne'),(300,100,'Umsatzsteuer erklärt durch Platform'),(300,120,'USt-ID LU20260743'))
        rules={'Platform':{'vat_ids':['LU20260743'],'aliases':['Platform']},'SellerOne':{'aliases':['SellerOne']}}
        r=extract_fields('\n'.join(x['text'] for x in d['rows']),rules,document=d)
        self.assertEqual(r['provider'],'SellerOne');self.assertFalse(r['identifiers'][0]['issuer_usable'])
        r=extract_fields('\n'.join(x['text'] for x in d['rows']),{'Platform':rules['Platform']},document=d)
        self.assertEqual(r['provider'],'')

    def test_shared_identifier_needs_name_and_cannot_merge_sellers(self):
        rules={'A':{'aliases':['SellerOne'],'vat_ids':['LU20260743']},'B':{'aliases':['SellerTwo'],'vat_ids':['LU20260743']}}
        self.assertEqual(extract_fields('VAT LU20260743',rules)['provider'],'')
        self.assertEqual(extract_fields('SellerTwo\nVAT LU20260743',rules)['provider'],'B')
        self.assertEqual(extract_fields('SellerOne SellerTwo\nVAT LU20260743',rules)['provider'],'')

    def test_recipient_or_carrier_name_does_not_override_explicit_seller(self):
        d=document((300,20,'Verkauft von SellerOne'),(30,200,'Lieferadresse'),(30,214,'Carrier Express'))
        r=extract_fields('\n'.join(x['text'] for x in d['rows']),{'S':{'aliases':['SellerOne']},'C':{'aliases':['Carrier']}},document=d)
        self.assertEqual(r['provider'],'S')

class AdditionalStructureTests(unittest.TestCase):
    def test_label_split_across_lines(self):
        d=document((30,20,'Gesamtsumme'),(30,32,'Brutto'),(220,32,'49,95'),
                   (30,70,'Rechnungs'),(30,82,'Nr:'),(220,82,'X-99'))
        r=recognize(d)
        self.assertEqual(r['values']['amount'],'49,95')
        self.assertEqual(r['values']['number'],'X-99')

    def test_carrier_only_alias_not_issuer_without_seller_heading(self):
        d=document((30,20,'Versand per CarrierExpress'),(30,60,'Rechnungsbetrag 25,00'))
        r=extract_fields('\n'.join(x['text'] for x in d['rows']),{'Carrier':{'aliases':['CarrierExpress']}},document=d)
        self.assertEqual(r['provider'],'')
