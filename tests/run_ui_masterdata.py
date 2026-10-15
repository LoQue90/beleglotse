import sys,tempfile,threading,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import app
from test_identifiers import invoice
from pypdf import PdfReader,PdfWriter
from pypdf.generic import DecodedStreamObject,NameObject
with tempfile.TemporaryDirectory(prefix='beleglotse-ui332-') as tmp:
 root=Path(tmp);folder=root/'Eingang';folder.mkdir();path=folder/'rechnung.pdf';invoice(path)
 reader=PdfReader(path);writer=PdfWriter();writer.append(reader);stream=DecodedStreamObject();stream.set_data(reader.pages[0].get_contents().get_data().replace(b'Gesamtbetrag',b'Betrag'));writer.pages[0][NameObject('/Contents')]=writer._add_object(stream);writer.write(path)
 app.LOCAL=root/'local.json';app.DATABASE=None
 server=app.LocalServer(('127.0.0.1',0),app.Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:result=subprocess.run(['node',str(ROOT/'tests/ui_masterdata.cjs'),f'http://127.0.0.1:{server.server_port}',str(root)],timeout=50)
 finally:server.shutdown();server.server_close();thread.join()
 sys.exit(result.returncode)
