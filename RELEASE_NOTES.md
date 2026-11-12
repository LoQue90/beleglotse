# 3.3.3

- Manuelle Belege im Verlauf mit optionalem PDF-Verweis und Notiz; gemeinsame fortlaufende Nummerierung und Dublettenprüfung.
- Nummernvergabe erst beim Speichern; veraltete Vorschauen werden abgewiesen.
- Einzelne Verlaufseinträge nach Bestätigung löschen; PDF, TSV und Nummernzähler bleiben erhalten.
- TSV-Beträge mit Tausenderpunkt und Dezimalkomma, z. B. 1.646,23 €.
- Verlaufssuche mit Originalnummer, Datum, Betrag und kombinierbaren Bereichsfiltern.
- Künstliche Trennungen in Rechnungsnummern und Datum werden anhand des PDF-Textes korrigiert.

## Windows

`BelegLotse-v3.3.3-Windows-EXE.zip` vollständig entpacken und `BelegLotse.exe` starten. Python ist enthalten. Alternativ das Windows-Paket mit `Start.cmd` verwenden (Python 3.10+ erforderlich).

Bestehende Jahresdateien bleiben verwendbar. Manuelle Einträge erzeugen keine TSV und verändern keine PDF. Das Löschen im Verlauf entfernt weder PDF/TSV noch eine Buchung in WISO; Belegnummern werden nicht wiederverwendet.
