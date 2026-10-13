# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Lorenz Uhlig
"""Reproduzierbares Release-Paket aus explizit erlaubten Programmdateien."""
from pathlib import Path
import argparse, hashlib, re, zipfile

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=('app.py','recognition.py','identifiers.py','index.html','bootstrap.py','Start.cmd','requirements.txt','VERSION','README.md','THIRD_PARTY.md','LICENSE')
SOURCE_ONLY=('.gitignore','CONTRIBUTING.md','CHANGELOG.md')

def files_in(directory):
    return [p for p in sorted((ROOT/directory).rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']

def archive(destination,files,prefix):
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in sorted(set(files)):
            relative=path.relative_to(ROOT).as_posix()
            if path.suffix.lower() in ('.pdf','.tsv','.sqlite','.belegdb') or path.name=='lokal.json':
                raise ValueError('Persönliche Datendatei in der Paketliste: '+relative)
            info=zipfile.ZipInfo(prefix+'/'+relative,date_time=(2026,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,path.read_bytes())
    with zipfile.ZipFile(destination) as z:
        if z.testzip():raise ValueError('Fehlerhaftes ZIP')

def build(output,tag=None):
    version=(ROOT/'VERSION').read_text().strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?',version):raise ValueError('Ungültige VERSION')
    if tag is not None and tag!='v'+version:raise ValueError('Git-Tag und VERSION stimmen nicht überein: '+tag+' / '+version)
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    runtime=[ROOT/x for x in RUNTIME]+files_in('vendor')
    source=runtime+[ROOT/x for x in SOURCE_ONLY]+files_in('scripts')+files_in('tests')+files_in('.github')
    paths=[output/f'BelegLotse-v{version}-Windows.zip',output/f'BelegLotse-v{version}-Source.zip']
    archive(paths[0],runtime,'beleglotse');archive(paths[1],source,'beleglotse')
    hashes=output/'SHA256SUMS.txt'
    hashes.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in paths),encoding='utf-8')
    return paths+[hashes]

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default=str(ROOT/'dist'));parser.add_argument('--tag')
    args=parser.parse_args()
    for path in build(args.output,args.tag):print(path)
