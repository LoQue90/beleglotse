# SPDX-License-Identifier: GPL-3.0-only
"""Windows entry point, with per-installation single-instance guard."""
import sys
import time
import webbrowser
from pathlib import Path


def main():
    import app
    if '--self-test' in sys.argv:
        import tempfile
        import tkinter as tk
        import pypdfium2 as pdfium
        from pypdf import PdfWriter, PdfReader
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp)/'check.pdf'
            writer=PdfWriter(); writer.add_blank_page(width=100,height=100)
            writer.encrypt('test',algorithm='AES-256'); writer.write(pdf)
            reader=PdfReader(pdf); assert reader.decrypt('test'); assert len(reader.pages)==1
            with pdfium.PdfDocument(pdf,password='test') as doc:
                page=doc[0]; bitmap=page.render(); image=bitmap.to_pil()
                image.save(Path(tmp)/'check.png'); image.close(); bitmap.close(); page.close()
            root=tk.Tk(); root.withdraw(); root.update(); root.destroy()
        for name in ['index.html','VERSION','accounts_ekr03.json']:
            assert (app.ROOT/name).is_file(), name
        print('EXE self-test OK')
        return
    lock = None
    try:
        if sys.platform == 'win32':
            import msvcrt
            lock = (app.DATA_ROOT / 'instance.lock').open('a+b')
            if lock.tell() == 0:
                lock.write(b' '); lock.flush()
            lock.seek(0)
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                for _ in range(30):
                    lock.seek(1)
                    url = lock.read().decode('ascii').strip()
                    if url.startswith('http://127.0.0.1:') and url.rsplit(':', 1)[-1].isdigit():
                        if '--no-browser' not in sys.argv: webbrowser.open(url)
                        return
                    time.sleep(.1)
                raise RuntimeError('BelegLotse wird bereits gestartet. Bitte kurz warten.')
            lock.seek(1); lock.truncate(); lock.flush()
        def ready(url):
            if lock:
                lock.seek(1); lock.write(url.encode('ascii')); lock.truncate(); lock.flush()
        app.main(on_ready=ready)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, str(exc), 'BelegLotse – Start fehlgeschlagen', 16)
        raise
    finally:
        if lock: lock.close()

if __name__ == '__main__':
    main()
