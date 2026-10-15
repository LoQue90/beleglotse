# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Lorenz Uhlig
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from recognition import extract_fields

class RecognitionTests(unittest.TestCase):
    def test_generic_invoice(self):
        text='Beispiel GmbH\nRechnungsdatum: 05.02.2026\nRechnungsnummer: RE-123\nNettobetrag: 100,00\nGesamtbetrag: 119,00 EUR'
        r=extract_fields(text,{})
        self.assertEqual((r['date'],r['number'],r['amount']),('2026-02-05','RE-123','119,00'))
    def test_custom_labels_and_supplier(self):
        rules={'Werkstatt':dict(aliases=['UST-123'],labels={'date':'Dokumenttag','number':'Vorgang','amount':'Endsumme'})}
        r=extract_fields('UST-123\nDokumenttag: 2026-03-01\nVorgang: A-9\nEndsumme: 14.99 EUR',rules)
        self.assertEqual((r['provider'],r['date'],r['number'],r['amount']),('Werkstatt','2026-03-01','A-9','14,99'))


    def test_repeated_total_with_same_value_is_unambiguous(self):
        result=extract_fields('Gesamtsumme Brutto: 6,19\nRechnungsbetrag: 6,19',{})
        self.assertEqual(result['amount'],'6,19')
        self.assertEqual(result['candidates']['amount'],['6,19'])
