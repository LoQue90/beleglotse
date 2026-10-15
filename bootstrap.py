# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Lorenz Uhlig
"""Richtet eine lokale Python-Umgebung ein und startet den Belegimport."""
from pathlib import Path
import subprocess
import sys
import venv
import hashlib
import json
import time

ROOT = Path(__file__).resolve().parent
CHECK = "import pypdfium2, PIL; import cryptography; from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes; assert tuple(int(p) for p in cryptography.__version__.split('.')[:2]) >= (3, 1)"


def main():
    if sys.version_info < (3, 10):
        print('Bitte Python 3.10 oder neuer installieren.')
        return 1
    started=time.perf_counter()
    environment = ROOT / '.venv'
    python = environment / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    try:
        if not python.exists():
            print('Lokale Python-Umgebung wird eingerichtet ...', flush=True)
            venv.EnvBuilder(with_pip=True).create(environment)
        stamp=environment / 'beleglotse-setup.json'
        identity={'requirements':hashlib.sha256((ROOT/'requirements.txt').read_bytes()).hexdigest(),
                  'python':str(python),'mtime':python.stat().st_mtime_ns,'check':CHECK}
        try:ready=json.loads(stamp.read_text())==identity
        except (OSError,ValueError):ready=False
        if not ready:
            check = subprocess.run([str(python), '-c', CHECK], capture_output=True)
            if check.returncode:
                print('PDF-Bibliotheken werden eingerichtet. Hierfuer wird einmalig Internet benoetigt.', flush=True)
                subprocess.run([str(python), '-m', 'pip', 'install', '--disable-pip-version-check', '-r', str(ROOT / 'requirements.txt')], check=True)
                subprocess.run([str(python), '-c', CHECK], check=True)
            stamp.write_text(json.dumps(identity),encoding='utf-8')
        print(f'Startvorbereitung: {time.perf_counter()-started:.2f} s',flush=True)
        code=subprocess.call([str(python), str(ROOT / 'app.py')], cwd=ROOT)
        if code:stamp.unlink(missing_ok=True)
        return code
    except (OSError, subprocess.CalledProcessError) as exc:
        print('Einrichtung fehlgeschlagen: ' + str(exc))
        print('Bitte Internetverbindung und Schreibrechte im App-Ordner pruefen und Start.cmd erneut ausfuehren.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
