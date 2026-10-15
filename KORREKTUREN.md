# Prüfung von Version 3.3.0

Umgesetzte Bereiche:

- Allgemeine Rechnungssteller- und Kennungserkennung, gemeinsame Bestätigung mehrerer Kennungen.
- Räumliche Feldzuordnung, bezahlte Gesamtsummen und bewusst gespeicherte Feldzuordnungen.
- Kopierbare PDF-Textebene und einzelne PDF erneut auswerten.
- Konten und Steuersätze in Jahresdateien, Standards und Belegüberschreibungen.
- Pflichtfeldmarkierungen und Null-Euro-Ablage ohne TSV-Zeile.
- Durchgängige Hell-/Dunkel-Farben, Symbolschalter und dunkle Voreinstellung.

Automatisierte Prüfung: `python -m unittest discover -s tests -v`.
Optionaler Oberflächentest mit Node.js und jsdom: `python tests/run_ui_masterdata.py`.

Die Tests verwenden synthetische Belege. Persönliche Rechnungen und Datenbanken werden nicht mitgeliefert.
