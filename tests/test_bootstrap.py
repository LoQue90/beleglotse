# SPDX-License-Identifier: GPL-3.0-only
import tempfile, unittest
from pathlib import Path
from unittest.mock import patch, Mock
import bootstrap

class BootstrapTests(unittest.TestCase):
    def test_verified_environment_skips_repeated_import_probe_and_recovers_after_error(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'requirements.txt').write_text('test')
            executable=root/'.venv'/('Scripts/python.exe' if bootstrap.sys.platform=='win32' else 'bin/python')
            executable.parent.mkdir(parents=True);executable.write_text('placeholder')
            with patch.object(bootstrap,'ROOT',root),patch.object(bootstrap.subprocess,'run',return_value=Mock(returncode=0)) as probe,patch.object(bootstrap.subprocess,'call',return_value=0) as start:
                self.assertEqual(bootstrap.main(),0);self.assertEqual(probe.call_count,1)
                self.assertEqual(bootstrap.main(),0);self.assertEqual(probe.call_count,1)
                (root/'requirements.txt').write_text('changed')
                bootstrap.main();self.assertEqual(probe.call_count,2)
                start.return_value=1;bootstrap.main()
                self.assertFalse((root/'.venv/beleglotse-setup.json').exists())
                start.return_value=0;bootstrap.main();self.assertEqual(probe.call_count,3)
