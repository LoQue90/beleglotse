# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Lorenz Uhlig
import sys, tempfile, unittest, zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import build_release

class PackageTests(unittest.TestCase):
    def test_build_contains_program_but_no_private_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths=build_release.build(tmp,tag='v'+(build_release.ROOT/'VERSION').read_text().strip())
            with zipfile.ZipFile(paths[0]) as z:
                names=z.namelist()
                self.assertIn('beleglotse/Start.cmd',names)
                self.assertIn('beleglotse/recognition.py',names)
                self.assertFalse(any(n.endswith(('.belegdb','.sqlite','.pdf','.tsv','lokal.json')) for n in names))
                self.assertFalse(any('/.github/' in n for n in names))
            with zipfile.ZipFile(paths[1]) as z:
                self.assertIn('beleglotse/.github/workflows/release.yml',z.namelist())
    def test_wrong_tag_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):build_release.build(tmp,tag='v0.0.0-wrong')

if __name__=='__main__':unittest.main()
