# SPDX-License-Identifier: GPL-3.0-only
import unittest, socket, threading, http.client, tempfile, time
from pathlib import Path
from unittest.mock import patch
import app
from recognition import extract_fields, pdf_text
from test_identifiers import invoice

class FieldRegressionTests(unittest.TestCase):
    def amount(self,text):
        return extract_fields(text,{'Test':{'labels':{'amount':['Gesamtsumme Brutto','Rechnungsbetrag (inklusive Umsatzsteuer)','Betrag']}}},selected_provider='Test')
    def test_date_in_payment_sentence_is_not_money(self):
        r=self.amount('Rechnungsbetrag (inklusive Umsatzsteuer) 4,06 EUR\nWir buchen den Betrag frühestens am 14.01.2026 ab.')
        self.assertEqual(r['candidates']['amount'],['4,06'])
    def test_bare_amount_without_currency(self):
        result=self.amount('Betrag 16,20')
        self.assertEqual(result['amount'],'16,20')
        hit=result['field_evidence']['amount'][0]
        self.assertEqual((hit['value'],hit['label'],hit['selected']),('16,20','Betrag',True))
        self.assertEqual(result['field_status']['amount'],'review')
    def test_date_only_is_not_money(self):
        for date in ['14.01.2026','14-01-2026','14/01/2026','2026-01-14']:
            self.assertEqual(self.amount('Betrag '+date)['amount'],'')
    def test_strong_total_beats_weak_amount(self):
        self.assertEqual(self.amount('Gesamtsumme Brutto 10,00\nBetrag 2,00')['amount'],'10,00')
    def test_conflicting_strong_totals_stay_open(self):
        self.assertEqual(self.amount('Gesamtsumme Brutto 10,00\nRechnungsbetrag (inklusive Umsatzsteuer) 11,00')['amount'],'')
    def test_net_and_tax_not_final_total(self):
        r=extract_fields('Rechnungsbetrag (ohne Umsatzsteuer) 10,00\nUmsatzsteuer 1,90\nRechnungsbetrag (inklusive Umsatzsteuer) 11,90',{})
        self.assertEqual(r['amount'],'11,90')
        self.assertEqual(extract_fields('Rechnungsbetrag (ohne Umsatzsteuer) 10,00',{})['amount'],'')
    def test_repeated_stacked_labels_not_invoice_numbers(self):
        r=extract_fields('Rechnungsnummer: TEST-42\nRechnungsnummer:\nRechnungsdatum:\nKundennummer:\nTEST-42\n01.01.2026',{})
        self.assertEqual(r['number'],'TEST-42')
    def test_signed_and_large_amounts(self):
        self.assertEqual(self.amount('Betrag -1.234,56')['amount'],'-1234,56')
    def test_layout_damage_falls_back(self):
        class Page:
            def extract_text(self,**kwargs):
                return 'Rechnungsreferenz M OL-12345' if kwargs else 'Rechnungsreferenz MOL-12345'
        class Reader:
            is_encrypted=False
            pages=[Page()]
        with patch('recognition.PdfReader',return_value=Reader()):
            text,_=pdf_text('ignored',False)
        self.assertIn('MOL-12345',text)
    def test_valid_layout_header_kept_despite_broken_other_lines(self):
        from recognition import safe_layout_lines
        plain='Rechnungsnummer:\nRechnungsdatum:\nRechnungsbetrag:\nFälliger Betrag\nINV-42\n28/05/2026\n52,69 EUR\n0,00 EUR\nVersandunternehmen'
        layout='Rechnungsnummer: INV-42\nRechnungsdatum: 28/05/2026\nRechnungsbetrag: 52,69 EUR\nFälliger Betrag 0,00 EUR\nVersand unternehmen'
        lines=safe_layout_lines(plain,layout)
        self.assertNotIn('Versand unternehmen',lines)
        r=extract_fields(plain,{},layout_lines=lines)
        self.assertEqual((r['number'],r['date'],r['amount']),('INV-42','2026-05-28','52,69'))
    def test_broken_layout_number_not_added(self):
        from recognition import safe_layout_lines
        plain='Rechnungsreferenz MOL-NL-12345\nRechnungsbetrag 1,70 EUR'
        layout='Rechnungsreferenz M OL-NL-12345\nRechnungsbetrag 1,70 EUR'
        r=extract_fields(plain,{},layout_lines=safe_layout_lines(plain,layout))
        self.assertEqual(r['candidates']['number'],['MOL-NL-12345'])
    def test_layout_conflict_is_not_silently_preferred(self):
        r=extract_fields('Rechnungsbetrag: 10,00',{},layout_lines=['Rechnungsbetrag: 11,00'])
        self.assertEqual(r['amount'],'')
        self.assertIn('mehrdeutig',r['note'])
    def test_positioned_columns(self):
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import DecodedStreamObject,NameObject
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'invoice.pdf';invoice(path)
            reader=PdfReader(path);writer=PdfWriter();writer.add_page(reader.pages[0])
            stream=DecodedStreamObject();stream.set_data(b'BT /F1 10 Tf 30 750 Td (Rechnungsnummer:) Tj 0 -25 Td (Rechnungsdatum:) Tj ET BT /F1 10 Tf 240 750 Td (TEST-42) Tj 0 -25 Td (01.02.2026) Tj ET')
            writer.pages[0][NameObject('/Contents')]=writer._add_object(stream)
            writer.write(path)
            text,_=pdf_text(path,False);r=extract_fields(text,{})
            self.assertEqual((r['number'],r['date']),('TEST-42','2026-02-01'))

class ServerRegressionTests(unittest.TestCase):
    def test_idle_connections_do_not_block_page_or_init(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(app,'DATABASE',None),patch.object(app,'LOCAL',Path(tmp)/'local.json'):
            server=app.LocalServer(('127.0.0.1',0),app.Handler)
            worker=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.02},daemon=True);worker.start()
            idle=socket.create_connection(server.server_address)
            try:
                self.assertTrue(server.ready.wait(1))
                for url in ['/','/api/init']:
                    c=http.client.HTTPConnection(*server.server_address,timeout=2)
                    try:c.request('GET',url);r=c.getresponse();self.assertEqual(r.status,200);r.read()
                    finally:c.close()
            finally:idle.close();server.shutdown();server.server_close();worker.join()
    def test_state_handlers_are_serialized(self):
        active=0;maximum=0;guard=threading.Lock()
        class Fake:
            @app.serialized
            def do_POST(self):
                nonlocal active,maximum
                with guard:active+=1;maximum=max(maximum,active)
                time.sleep(.02)
                with guard:active-=1
        threads=[threading.Thread(target=Fake().do_POST) for _ in range(4)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertEqual(maximum,1)

class StartupStateTests(unittest.TestCase):
    def test_loading_can_be_skipped_without_waiting_for_year_file(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(app,'DATABASE',None),patch.object(app,'LOCAL',Path(tmp)/'local.json'),patch.object(app,'STARTUP',{'loading':True,'error':''}),patch.object(app,'STARTUP_CANCEL',threading.Event()):
            server=app.LocalServer(('127.0.0.1',0),app.Handler)
            worker=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.01},daemon=True);worker.start()
            try:
                conn=http.client.HTTPConnection(*server.server_address,timeout=2)
                conn.request('GET','/api/init');response=conn.getresponse()
                import json
                state=json.loads(response.read());self.assertTrue(state['startup']['loading']);conn.close()
                conn=http.client.HTTPConnection(*server.server_address,timeout=2)
                conn.request('POST','/api/startup/skip',body='{}',headers={'X-Token':state['token'],'Content-Type':'application/json'})
                response=conn.getresponse();self.assertEqual(response.status,200);response.read();conn.close()
                self.assertFalse(app.STARTUP['loading']);self.assertTrue(app.STARTUP_CANCEL.is_set())
            finally:server.shutdown();server.server_close();worker.join()
