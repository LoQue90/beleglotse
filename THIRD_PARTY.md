# Drittanbieter-Komponenten

`vendor/` enthält pypdf 6.1.1. Die vollständige BSD-3-Clause-Lizenz liegt unter `vendor/pypdf-6.1.1.dist-info/licenses/LICENSE` und wird in die Pakete aufgenommen.

Beim ersten Start installiert `bootstrap.py` die Bibliotheken aus `requirements.txt` in eine lokale Python-Umgebung: cryptography, pypdfium2 und Pillow. Deren Paketmetadaten und Lizenztexte sind Teil der jeweiligen Installation. Tesseract wird separat installiert und ist nicht im Download enthalten.

Die persönlichen Jahresdateien und Rechnungen sind keine Programmkomponenten und werden nicht in Release-Pakete aufgenommen.
