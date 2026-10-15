# 3.3.1

- Windows-EXE mit eingebettetem Python, Browserstart und Mehrfachstartschutz.
- Maßeinheiten werden nicht mehr als Rechnungsstellernamen vorgeschlagen.
- Windows-Build prüft den Start der fertigen EXE vor Veröffentlichung.

# Änderungen

## 3.3.0

- PDF-Fundstellen mit auswählbarer Textebene, merkbaren Feldzuordnungen und verbesserter allgemeiner Erkennung.
- Rechnungsstellervorschläge mit gemeinsamer Bestätigung von USt-ID und Steuernummer; optionale Sammelzuordnung.
- 341 EKR03-Konten, Kontenimport und bearbeitbare Steuersätze in der Jahresdatei; Standards je Rechnungssteller und Änderungen je Beleg.
- WISO-TSV mit Steuersatz und ohne NULL-Spalte; Null-Euro-Belege nur nummerieren und ablegen.
- Lokale Fehlermeldungen, Pflichtfeldmarkierungen, Sammelprüfung und Entfernen aus der Prüfliste.
- Hell-/Dunkel-Symbol ganz rechts, kleinere Versionsanzeige und Dark Mode als Standard; gespeicherte Auswahl bleibt erhalten.
- Einzelne PDF direkt neben dem Speichern des Rechnungsstellerstandards erneut auswerten.
- 96 automatisierte Tests und zusätzlicher lokaler Oberflächentest erfolgreich.

## 3.3.0-test5

- Einheitliche Hell-/Dunkel-Farben für Seitenflächen, Formulare und Dialoge; Umschalten per Sonnen-/Mondsymbol.
- Direkt neben dem Speichern eines Rechnungsstellerstandards nur die geöffnete PDF erneut auswerten.

# 3.3.0-test4

- Fehlende Pflichtfelder ausgewählter Belege rot markieren, bis sie ausgefüllt sind; zum ersten fehlenden Feld springen.
- Null-Euro-Belege nummerieren, ablegen und im Verlauf speichern, ohne TSV-Zeile; bei ausschließlich Null-Euro-Belegen keine TSV erstellen. Negative Beträge weiterhin exportieren.
- Darstellung Hell, Dunkel oder Systemeinstellung; Auswahl lokal und über App-Neustarts hinweg speichern. PDF-Seiten bleiben im Original.

# 3.3.0-test3

Kontenvorlage und Jahresdatenbank-Verwaltung, bearbeitbare Steuersätze, Belegüberschreibungen, korrigiertes TSV-Format, gemeinsame Kennungsbestätigung sowie Verbesserungen der Prüfliste und Fehlermeldungen umgesetzt.


## 3.3.0-test2 (lokale Testversion)

- Punktierte Rechtsformen und ausländische Kennungen vor nachfolgenden Feldbeschriftungen erkennen.
- Geteilte Kennungen räumlich lokalisieren; Abrechnungsrollen an Spaltengrenzen begrenzen.
- Firmennamen auch ohne Kennung als prüfpflichtige Vorschläge anbieten.
- Bereits bezahlte Abschlussbeträge mit örtlich passender Netto-/Steuerrechnung als Vorschläge erkennen.
- Ausdrückliche Sammelzuordnung pro Rechnungssteller für gemeinsame Kennungen.
- Bestätigte Feldzuordnungen speichern, anwenden und je Feld löschen; Konflikte und OCR bleiben prüfpflichtig.
- Skalierende auswählbare Textebene über der PDF-Vorschau.
- Neue Rechnungssteller aus dem geöffneten Beleg vorausfüllen, Alternativen und Fundstellen anzeigen.
- Testbereinigung beibehalten; sechs gezielte allgemeine Regressionstests ergänzt.

## 3.3.0-test1 (lokale Testversion)

- Eigenständiges Dokumentmodell mit Wortpositionen, Seiten und Herkunft aus PDF oder OCR.
- Gemeinsame Feldlogik für räumliche Beschriftungszuordnung, Tabellen, mehrzeilige Begriffe, Monatsnamen und getrennte Betragsrollen.
- Eigene Feldbegriffe ergänzen die Standards; unklare gleichwertige Treffer bleiben offen.
- Verkäufer-, Empfänger-, Plattform- und weitere ausdrücklich beschriftete Rollen berücksichtigen; geteilte Kennungen nicht allein zuordnen.
- Anklickbare Fundstellen mit Seitenwechsel, Markierung und manueller Wertübernahme in der Browseroberfläche.
- PDF-Daten während einer Sitzung begrenzt zwischenspeichern; Regeln werden weiterhin neu angewendet.
- Jahresdatei beim Start im Hintergrund öffnen, Wartephase überspringbar; Startzeiten protokollieren.
- Erfolgreiche Abhängigkeitsprüfung zwischenspeichern und bei Änderungen bzw. Fehlern erneuern.
- Zusätzliche synthetische Regressionstests; persönliche Rechnungen bleiben außerhalb der Pakete.

## 3.2.1-test2 (lokale Testversion)

- Gültige räumliche Feldzuordnungen ergänzen, auch wenn die Layout-Auswertung an anderen Stellen der Seite abweicht.
- Beschädigte Layout-Zeilen einzeln ausschließen statt gültige Kopfdaten mitzuverwerfen.
- Räumliche Zusatzinformationen bei manueller Rechnungsstellerwahl und erneuter Auswertung erhalten.

## 3.2.1-test1 (lokale Testversion)

- Unbenutzte Browserverbindungen blockieren den Seitenaufbau nicht mehr; Browserstart erst nach Bereitschaft des Servers.
- Datenzugriffe und Änderungen bleiben innerhalb der App serialisiert.
- PDF-Layout zur Feldzuordnung nutzen, mit Rückfall auf Originaltext bei beschädigten Wörtern.
- Feldbeschriftungen nicht als Rechnungsnummer übernehmen.
- Datumsangaben und Prozentsätze nicht als Geldbetrag lesen; Nettobeträge von Endbeträgen unterscheiden.
- Eindeutige Endbetragsbezeichnungen gegenüber allgemeinen Begriffen bevorzugen; gleichwertige Konflikte weiterhin offenlassen.
- Verwendete Feldbezeichnungen in den Hinweisen anzeigen.

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
