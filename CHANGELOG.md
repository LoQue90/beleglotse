# Änderungen

## 3.2.0

- Rechnungssteller aus USt-IDs und Steuernummern vorschlagen, nach Kennung gruppieren und erst nach Bestätigung speichern.
- Räumlich zugeordnete Firmennamen, alternative Namen und Beispielbelege zur Prüfung anzeigen.
- Bestätigte Kennungen bei der Zuordnung vor Textmerkmalen bevorzugen; Mehrfachtreffer offenlassen.
- Eigene Unternehmenskennungen ausschließen und doppelte Zuordnung einer Kennung verhindern.
- Rechnungssteller direkt im Regelfenster auswählen oder neu anlegen.
- Kennungen beim Jahreswechsel übernehmen; fehlende OCR und nicht lesbare Belege im Scan melden.

## 3.1.1

- Neue Rechnungssteller direkt aus der Auswahl dauerhaft anlegen, mit eigenem Formular.
- Namen als editierbaren Vorschlag für Erkennungsmerkmale vorbelegen.
- Leere Merkmale beim Bearbeiten und Speichern deutlich kennzeichnen.
- Bestehende Rechnungssteller beim Neuanlegen vor versehentlichem Überschreiben schützen.
- Oberfläche und README verwenden einheitlich „Rechnungssteller“.

## 3.1.0

- Neue Jahresdateien ohne fest vorgegebene Anbieter oder Konten; bestehende Stammdaten bleiben erhalten.
- Anbietererkennung ausschließlich über gespeicherte Merkmale, wahlweise UND/ODER und Ausschlussbegriffe.
- Anbieterbezogene Feldregeln erst nach eindeutiger oder manueller Auswahl; keine eingebauten Anbieter-Sonderfälle.
- Nachvollziehbare Trefferanzeige und erneute Auswertung nach Anbieterwahl.
- Benutzerbezogene Kontenzuordnungen aus der README entfernt.

## 3.0.0

- Eigene Jahresdatei mit Stammdatenübernahme aus einem Vorjahr.
- Konten, Anbieterregeln und Einstellungen übernehmen, ohne verarbeitete Belege zu kopieren.
- Mehrere alternative Feldbezeichnungen je Rechnungssteller für Datum, Nummer und Betrag.
- Anbieter-Dropdown mit vollständiger Liste und separater Suche.
- Konfigurierbare Dateinamen sowie Präfix, Jahresdarstellung und Mindeststellen der Belegnummer.
- Ablage standardmäßig direkt unter Eingang/verbucht; optionale Monatsordner.
- Rechnerbezogene Import- und Ablagepfade je Jahresdatei.
- Windows-Tests und automatische Release-Pakete über GitHub Actions.

## 2.0.0

Allgemeine Erkennung, lokale OCR, Sachkontenverwaltung, Anbieterregeln, PDF-Vorschau, Belegverlauf und VTUER-Nummerierung.

## 1.0.1

Automatische Einrichtung der Kryptografie-Bibliothek und verständliche Hinweise für verschlüsselte PDFs.

## 1.0.0

Erster lokaler Import für Post, DHL und Mollie mit WISO-TSV und Belegablage.

### Lizenz vor Erstveröffentlichung

- Eigener BelegLotse-Code auf GPL-3.0-only umgestellt; Drittanbieter-Lizenzen bleiben erhalten.
