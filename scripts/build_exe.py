# SPDX-License-Identifier: GPL-3.0-only
"""Build and smoke-test the actual Windows executable before packaging."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def main():
    if sys.platform != 'win32': raise RuntimeError('EXE muss unter Windows gebaut werden.')
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir', '--console',
           '--name', 'BelegLotse', '--distpath', str(ROOT/'build/exe'), '--workpath', str(ROOT/'build/pyinstaller'),
           '--specpath', str(ROOT/'build'), '--paths', str(ROOT/'vendor'),
           '--collect-all', 'pypdfium2', '--collect-all', 'pypdfium2_raw', '--collect-all', 'cryptography']
    for name in ['index.html', 'VERSION', 'accounts_ekr03.json']:
        cmd += ['--add-data', str(ROOT/name)+':.']
    subprocess.run(cmd+[str(ROOT/'launcher.py')], cwd=ROOT, check=True)
    bundle = ROOT/'build/exe/BelegLotse'
    subprocess.run([str(bundle/'BelegLotse.exe'), '--self-test'], check=True, timeout=60)
    # Exercise the HTTP server and second-instance handling.
    with tempfile.TemporaryDirectory() as tmp:
        with open(Path(tmp)/'startup.log', 'w+', encoding='utf-8') as log:
            proc = subprocess.Popen([str(bundle/'BelegLotse.exe'), '--no-browser'], cwd=tmp, stdout=log, stderr=log)
            try:
                for _ in range(120):
                    if proc.poll() is not None: raise RuntimeError('EXE beendet: '+(Path(tmp)/'startup.log').read_text())
                    try:
                        url=(bundle/'instance.lock').read_bytes()[1:].decode('ascii').strip()
                        if url:
                            with urllib.request.urlopen(url, timeout=2) as response:
                                assert b'BelegLotse' in response.read()
                            break
                    except (OSError, ValueError): pass
                    time.sleep(.5)
                else: raise RuntimeError('EXE startet nicht innerhalb von 60 Sekunden.')
                second=subprocess.run([str(bundle/'BelegLotse.exe'), '--no-browser'], timeout=15)
                assert second.returncode == 0, 'Mehrfachstart fehlgeschlagen'
            finally:
                proc.terminate(); proc.wait(timeout=15)
    (bundle/'instance.lock').unlink(missing_ok=True)
    for name in ['README.md','LICENSE','THIRD_PARTY.md','VERSION']:
        shutil.copy2(ROOT/name,bundle/name)
    version=(ROOT/'VERSION').read_text().strip()
    target=ROOT/'dist'/f'BelegLotse-v{version}-Windows-EXE.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(bundle.rglob('*')):
            if path.is_file(): z.write(path,'BelegLotse/'+path.relative_to(bundle).as_posix())
    with zipfile.ZipFile(target) as z: assert z.testzip() is None
    with (ROOT/'dist/SHA256SUMS.txt').open('a',encoding='utf-8') as f:
        f.write(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name+'\n')
    print(target)

if __name__ == '__main__': main()
