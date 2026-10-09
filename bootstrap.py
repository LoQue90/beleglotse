# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Lorenz Uhlig
"""Richtet eine lokale Python-Umgebung ein und startet den Belegimport."""
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent
CHECK = "import pypdfium2, PIL; import cryptography; from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes; assert tuple(int(p) for p in cryptography.__version__.split('.')[:2]) >= (3, 1)"


def main():
    if sys.version_info < (3, 10):
        print('Bitte Python 3.10 oder neuer installieren.')
        return 1
    environment = ROOT / '.venv'
    python = environment / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    try:
        if not python.exists():
            print('Lokale Python-Umgebung wird eingerichtet ...', flush=True)
            venv.EnvBuilder(with_pip=True).create(environment)
        check = subprocess.run([str(python), '-c', CHECK], capture_output=True)
        if check.returncode:
            print('PDF-Bibliotheken werden eingerichtet. Hierfuer wird einmalig Internet benoetigt.', flush=True)
            subprocess.run([str(python), '-m', 'pip', 'install', '--disable-pip-version-check', '-r', str(ROOT / 'requirements.txt')], check=True)
            subprocess.run([str(python), '-c', CHECK], check=True)
        return subprocess.call([str(python), str(ROOT / 'app.py')], cwd=ROOT)
    except (OSError, subprocess.CalledProcessError) as exc:
        print('Einrichtung fehlgeschlagen: ' + str(exc))
        print('Bitte Internetverbindung und Schreibrechte im App-Ordner pruefen und Start.cmd erneut ausfuehren.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
