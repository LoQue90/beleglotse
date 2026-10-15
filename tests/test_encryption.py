# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Lorenz Uhlig
import sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
import recognition
from pypdf import PdfWriter

class EncryptedPdfTests(unittest.TestCase):
    def create_pdf(self, path, algorithm, password=''):
        writer=PdfWriter();writer.add_blank_page(width=300,height=200)
        writer.encrypt(user_password=password,owner_password='owner-secret',algorithm=algorithm)
        writer.write(path)
    def test_aes_without_open_password(self):
        with tempfile.TemporaryDirectory() as folder:
            for algorithm in ['AES-128','AES-256']:
                with self.subTest(algorithm=algorithm):
                    path=Path(folder)/'invoice.pdf';self.create_pdf(path,algorithm)
                    result=app.extract(path,ocr=False)
                    self.assertIn('Kein Text erkannt',result['note'])
    def test_password_required_message(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'invoice.pdf';self.create_pdf(path,'AES-256','secret')
            with self.assertRaisesRegex(ValueError,'Öffnungspasswort'):app.extract(path,ocr=False)
    def test_missing_dependency_message(self):
        with patch.object(recognition,'PdfReader',side_effect=recognition.DependencyError('cryptography>=3.1 is required')):
            with self.assertRaisesRegex(ValueError,'Start.cmd'):app.extract(Path('dummy.pdf'),fingerprint='dependency-test')

if __name__=='__main__':unittest.main()
