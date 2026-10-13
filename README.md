# BelegLotse

Eingangsrechnungen lokal aus PDFs erfassen, prüfen, als WISO-TSV exportieren und geordnet ablegen. Die Bedienung erfolgt im Browser, die Verarbeitung auf deinem Windows-Rechner.

**Rechnungen einlesen. Zuordnen. Ablegen.**

## Start unter Windows

1. Das **Windows-ZIP** vollständig in einen beschreibbaren Ordner entpacken.
2. Python 3.10 oder neuer installieren, falls noch nicht vorhanden. Im Setup „Add python.exe to PATH“ aktivieren.
3. `Start.cmd` doppelklicken. Beim ersten Start werden benötigte Bibliotheken über das Internet eingerichtet.
4. Der Standardbrowser öffnet die App. Das Konsolenfenster während der Arbeit geöffnet lassen; zum Beenden schließen oder Strg+C drücken.

Das Paket ist ein Python-Startpaket, keine eigenständige EXE. Nach der Einrichtung ist für die Belegverarbeitung kein Internet nötig. Es wird kein Cloud-KI-Dienst verwendet.

## Eine Datei pro Buchungsjahr

Über **„Neues Jahr anlegen“** werden Buchungsjahr und Dateiname festgelegt, zum Beispiel `Belege-2026.belegdb`. Die Jahresdatei enthält:

- Sachkonten und Rechnungsstellerstandards
- Erkennungsregeln und gemeinsame Einstellungen
- Nummernstand, verarbeitete Belege und Duplikatprüfung

Die PDFs bleiben separat in deinen Belegordnern.

Beim Anlegen von 2027 kannst du `Belege-2026.belegdb` als Vorlage auswählen. Konten, Rechnungsstellerregeln und Einstellungen werden übernommen. **Der Belegverlauf wird nicht kopiert.** Mit aktivierter Option „jährlicher Neustart“ beginnt die neue Nummerierung bei 001; andernfalls wird der letzte Nummernstand der Vorlage fortgeführt. Eine Änderung dieser Option setzt die Nummern der bereits geöffneten Datei nicht zurück.

**„Jahresdatei öffnen“** wechselt zwischen den Jahren. Die zuletzt verwendete Datei wird beim nächsten Programmstart wieder geöffnet. Ist sie nicht verfügbar, kannst du eine andere Datei auswählen; es wird keine leere Ersatzdatei angelegt. Die Dateiendung `.belegdb` ist eine normale SQLite-Datenbank.

### Cloud-Synchronisierung

Die Jahresdatei darf in einem lokal synchronisierten Cloud-Ordner liegen. Sie muss immer lokal verfügbar sein. Nur auf einem Rechner gleichzeitig verwenden. Vor einem Rechnerwechsel die App schließen und die vollständige Synchronisierung abwarten. Gleichzeitige Bearbeitung verschiedener Cloud-Kopien kann zu Konflikten führen; die App ist kein Mehrbenutzer-Server.

Import- und Ablagepfade werden pro Jahresdatei und Rechner in `lokal.json` gespeichert. Diese lokale Konfiguration nicht zwischen Rechnern synchronisieren. Historische PDF-Verweise enthalten den ursprünglichen Dateipfad; bei anderen Laufwerksbuchstaben lassen sie sich gegebenenfalls nicht direkt öffnen.

## Import und Ablage

Typischer Ablauf für 2026:

| Zweck | Ordner |
|---|---|
| Import | `2026/Eingang` |
| Ablage | `2026/Eingang/verbucht` |

Nach Auswahl eines Eingangsordners wird dessen Unterordner `verbucht` als Ablage vorgeschlagen, sofern noch kein Ziel eingetragen ist. Der Ablageordner darf fehlen und wird beim erfolgreichen Export angelegt. Eingelesen werden nur PDFs direkt im Eingangsordner, **keine Unterordner**. Bereits abgelegte Dateien in `verbucht` werden daher nicht erneut eingelesen.

Standardmäßig entstehen keine weiteren Unterordner. Wer möchte, kann zusätzliche Jahr-/Monat-Unterordner unter Einstellungen aktivieren.

1. „PDFs einlesen“ anklicken.
2. Datum, Rechnungssteller, Originalnummer, Rechnungssumme und Konten prüfen. „PDF / Regel“ zeigt den Beleg neben den Eingabefeldern.
3. Rechnungssteller über das Dropdown wählen. Beim Öffnen stehen alle Rechnungssteller zur Auswahl; das separate Suchfeld filtert die Liste. Über „Neuen Rechnungssteller anlegen“ öffnet sich ein Formular. „Speichern & auswählen“ speichert den Rechnungssteller dauerhaft in der Jahresdatei und wählt ihn aus.
4. Jeden ausgewählten Beleg als „Geprüft“ markieren. Änderungen heben die Markierung wieder auf.
5. „Exportvorschau erstellen“ zeigt die Reihenfolge, Belegnummern, Dateinamen und TSV-Zeilen.
6. Vorschau bestätigen und „TSV erstellen & PDFs verschieben“ anklicken.
7. Die erzeugte TSV selbst in WISO importieren.

Belege werden innerhalb eines Exports nach Rechnungsdatum aufsteigend sortiert. Bei gleichem Datum entscheidet der ursprüngliche Dateiname. Weicht das Rechnungsjahr von der Jahresdatei ab, muss dies in der Zeile gesondert bestätigt werden. Die interne Belegnummer gehört dabei zum **Buchungsjahr der Jahresdatei**, nicht zum abweichenden Rechnungsjahr.

## Sachkonten und Rechnungssteller

Unter „Konten & Rechnungssteller“ kannst du Sachkonten mit Nummer und Beschreibung anlegen. Bestehende Kontonummern können eine geänderte Beschreibung erhalten. Die Kontenliste ist bei der Belegprüfung durchsuchbar.

Neue Jahresdateien starten ohne vorgegebene Rechnungssteller, Sachkonten oder Geldkonten. Lege deine Stammdaten selbst an oder übernimm sie beim Anlegen aus einer vorhandenen Jahresdatei. Bereits gespeicherte Daten bleiben beim Programmupdate erhalten.

Sachkonto und Geldkonto können je Rechnungssteller gespeichert und pro Beleg geändert werden. Ein Rechnungssteller lässt sich auch ohne Kontozuordnung anlegen; vor dem Export müssen beide Konten ausgefüllt sein. Buchungstext ist der eingetragene Rechnungssteller.

Eine Änderung des Sachkontos in der Tabelle gilt zunächst nur für den Beleg. **„Als Standard für diesen Rechnungssteller speichern“** in der PDF-Vorschau übernimmt die Zuordnung für zukünftige Einlesevorgänge. So verändert eine Ausnahme nicht automatisch den Standard.

## Alternative Feldbezeichnungen

Jeder Rechnungssteller kann mehrere alternative Feldbezeichnungen für Datum, Rechnungsnummer und Gesamtbetrag haben, jeweils **eine Bezeichnung pro Zeile**. Beispiel für die Rechnungssumme:

```text
Gesamtsumme Brutto
Rechnungsbetrag
Gesamtbetrag
Betrag
```

Diese Bezeichnungen sind Alternativen: Findet die App einen eindeutigen Wert, schlägt sie ihn vor. Mehrere Treffer mit identischem Wert sind unproblematisch. Bei unterschiedlichen Werten bleibt das Feld zur Klärung leer und die möglichen Werte werden genannt.

Der Wert muss in derselben oder direkt nachfolgenden Zeile hinter der Bezeichnung stehen. Leer lassen bedeutet allgemeine Erkennung. Eigene Feldbezeichnungen ersetzen die allgemeine Erkennung für das betreffende Feld; sie werden nicht stillschweigend mit anderen Summenbegriffen vermischt.

## Rechnungssteller erkennen

### Stammdaten aus Belegen vorschlagen lassen

1. Unter **Einstellungen** eigene USt-IDs und Steuernummern eintragen. Diese Kennungen werden bei der Rechnungsstellererkennung ausgeschlossen. Steuernummern brauchen ein Land, beispielsweise `DE:123/456/78901`.
2. Eingangsordner auswählen und **„Rechnungssteller vorschlagen“** anklicken.
3. Die App gruppiert Belege nach gefundenen Kennungen und schlägt Firmennamen vor. Soweit im PDF verfügbar, nutzt sie die räumliche Nähe zwischen Kennung und Firmenname. Beispielbelege und Textfundstellen lassen sich direkt öffnen; alternative Namen werden angezeigt.
4. Namen und Kennung anhand des Belegs prüfen. Einen neuen Namen eintragen oder einen vorhandenen Rechnungssteller auswählen. Sachkonto und Geldkonto können gleich ergänzt werden. Bei Steuernummern das Land prüfen beziehungsweise ergänzen.
5. Jeden gewünschten Vorschlag ausdrücklich bestätigen und speichern. **Unbestätigte Vorschläge werden nicht als Stammdaten übernommen.** USt-ID und Steuernummer desselben Unternehmens können nacheinander demselben Rechnungssteller zugeordnet werden.
6. **„Belege mit bestätigten Stammdaten neu einlesen“** anklicken und anschließend die Buchungsangaben prüfen.

Kennungen und Namen sind Vorschläge, keine amtlich geprüften Unternehmensdaten. Auf einer Rechnung können auch Kennungen des Empfängers oder einer Abrechnungsstelle stehen. Eigene sowie ausdrücklich als Empfängerangabe erkannte Kennungen werden ausgeschlossen. Belege ohne verwendbare Kennung und Lesefehler erscheinen gesondert mit Hinweisen. Für Scans ohne Text wird Tesseract benötigt.

USt-IDs und Steuernummern werden getrennt gespeichert und beim Anlegen eines Folgejahres als Stammdaten übernommen. Eine Kennung kann nicht gleichzeitig zwei Rechnungsstellern zugewiesen werden. Deutsche USt-IDs werden auch ohne Feldbezeichnung gesucht; andere Länderformate benötigen eine passende USt-ID-/VAT-Bezeichnung. Die Erkennung deckt nicht jedes internationale Steuerformat ab. Bei Steuernummern ohne eindeutiges Land kann unter Einstellungen ein Standardland angegeben werden.

### Reihenfolge der Zuordnung

Zuerst werden gespeicherte USt-IDs und Steuernummern verglichen; Leerzeichen und übliche Trennzeichen werden vereinheitlicht. **Eindeutige Kennungstreffer haben Vorrang vor bloßen Textmerkmalen.** Passen Kennungen mehrerer Rechnungssteller, bleibt die Auswahl offen. Ohne Kennungstreffer greifen die gespeicherten Textregeln:

- **ODER:** Mindestens ein Erkennungsmerkmal muss vorkommen.
- **UND:** Alle Erkennungsmerkmale müssen vorkommen.
- **Ausschlussbegriffe:** Ein gefundener Ausschluss verhindert die automatische Zuordnung zu diesem Rechnungssteller, auch bei einer passenden Kennung.
- Ohne Kennungen und Textmerkmale erfolgt keine automatische Zuordnung. Beim Anlegen wird der Name als editierbarer Textvorschlag vorbelegt. Ohne Merkmale erscheint „Keine automatische Erkennung eingerichtet.“

Textmerkmale werden im gesamten PDF-Text gesucht. Ihre Position wird bei dieser Textsuche nicht gewichtet. Die räumliche Auswertung dient den Namensvorschlägen im Einrichtungsscan. Summenbezeichnungen entscheiden nicht über den Rechnungssteller.

Erst nach eindeutiger oder manueller Auswahl werden Feldregeln und Kontozuordnungen angewendet. Unter **„PDF / Regel“** zeigt die App passende Kennungen, Texttreffer und Ausschlüsse. Dort kannst du den Rechnungssteller direkt auswählen oder neu anlegen.

Nach manueller Rechnungsstellerwahl werden Datum, Rechnungsnummer, Betrag, Währung und Konten erneut vorgeschlagen. Bereits bearbeitete oder geprüfte Belege lösen vorher eine Rückfrage aus. Die Geprüft-Markierung wird aufgehoben. Neu gespeicherte Regeln lassen sich mit **„Mit gewähltem Rechnungssteller erneut auswerten“** direkt auf den geöffneten Beleg anwenden.

Erneutes Einlesen des gesamten Ordners ersetzt ungespeicherte Zeilenkorrekturen. Es gibt keine KI, die aus jeder Korrektur automatisch eine Regel erstellt.

## Dateinamen und Belegnummern einstellen

Unter Einstellungen lässt sich das Dateinamensschema frei festlegen:

| Platzhalter | Inhalt |
|---|---|
| `{belegnummer}` | Eigene Belegnummer, z. B. VTUER26001 |
| `{rechnungsnummer}` | Originalnummer des Lieferanten |
| `{aussteller}` | Rechnungssteller |
| `{datum}` | Rechnungsdatum als JJJJ-MM-TT |
| `{jahr}` | Zweistelliges Buchungsjahr |
| `{jahr4}` | Vierstelliges Buchungsjahr |

Beispiele:

```text
{belegnummer}_{aussteller}.pdf
{datum}_{aussteller}_{rechnungsnummer}.pdf
```

Die eigene Belegnummer hat ein einstellbares Präfix, eine Jahresdarstellung (ohne Jahr, zwei- oder vierstellig) und eine Mindestanzahl von Nummernstellen. Die Standardvorgabe ergibt `VTUER26001`. Führende Nullen werden automatisch ergänzt. Eine Vorschau zeigt das Ergebnis.

Nummern werden erst beim erfolgreichen Export verbraucht. Später hinzugefügte ältere Rechnungen erhalten die nächste freie Nummer; abgelegte Dateien werden nicht rückwirkend umnummeriert. Änderungen des Schemas betreffen nur künftige Exporte.

Ungültige Windows-Zeichen werden ersetzt. Ordnerpfade im Dateinamensschema sind nicht erlaubt. Falls das Schema die Originalnummer benötigt, muss sie ausgefüllt sein. Bestehende Zieldateien werden nicht überschrieben; bei einem nicht eindeutigen Schema muss der Name korrigiert werden.

Die Nummer in der TSV ist unabhängig vom Dateinamen wählbar: eigene Belegnummer oder Original-Rechnungsnummer. Beide bleiben im Verlauf gespeichert.

## Gescannte und verschlüsselte PDFs

Text-PDFs werden direkt gelesen. Für Seiten ohne ausreichenden Text lässt sich lokale OCR einschalten. Dafür muss **Tesseract** separat unter Windows installiert sein, mit deutschen oder englischen Sprachdaten. Die App sucht die Installation automatisch; alternativ unter Einstellungen `tesseract.exe` auswählen. Der PDF-Renderer wird beim App-Start eingerichtet.

OCR benötigt etwas Zeit und kann sich bei Zahlen oder Buchstaben irren. Ergebnisse immer prüfen. Fehlt Tesseract, ist weiterhin manuelle Erfassung möglich.

Verschlüsselte PDFs ohne Öffnungspasswort werden unterstützt. Für PDFs, die ein Passwort zum Öffnen verlangen, wird eine entsperrte Kopie benötigt. Es werden keine Rechnungsinhalte an Online-Dienste gesendet.

## WISO-TSV

UTF-8 ohne BOM, Tabulatoren, Windows-Zeilenenden und keine Kopfzeile:

| Spalte | Inhalt |
|---|---|
| 1 | Ausgabe |
| 2 | Datum TT.MM.JJJJ |
| 3 | Gewählte eigene oder originale Rechnungsnummer |
| 4 | Rechnungssteller |
| 5 | Betrag, z. B. 6,19 € |
| 6 | NULL |
| 7 | Sachkontonummer |
| 8 | Geldkontonummer |

Nur EUR; keine automatische Währungsumrechnung. Negative Beträge und Nullbeträge bleiben erhalten. Die App entscheidet nicht über steuerliche Behandlung oder Zahlungszeitpunkt. Das Format entspricht der bereitgestellten WISO-Vorlage; den ersten tatsächlichen Import in WISO prüfen.

## Duplikate und Sicherungen

Duplikatprüfung und Verlauf gelten für die aktuell geöffnete Jahresdatei. Doppelte PDF-Inhalte und dieselbe Kombination aus Rechnungssteller und Originalnummer werden blockiert. Fehlt die Originalnummer, ist nur die Inhaltsprüfung möglich. Andere Jahresdateien werden nicht durchsucht.

Vor dem Entfernen eines Originals werden die Zielkopie per SHA-256 geprüft, die TSV geschrieben und der Datenbankeintrag gespeichert. Bei normalen Schreibfehlern werden neue Dateien zurückgenommen. Kann ein Original nicht entfernt werden, meldet die App das; der Beleg bleibt als verarbeitet gespeichert.

Bei Stromausfall oder erzwungenem Programmabbruch können bereits erzeugte Dateien ohne abschließenden Datenbankeintrag zurückbleiben. Vor Wiederholung Ablage und WISO prüfen. Jahresdateien und PDF-Ablage regelmäßig sichern; Cloud-Synchronisierung allein ersetzt keine Sicherung.

## Umstieg von Version 2

Die neue Version kann in einen separaten Programmordner entpackt werden. Deine bisherige Datenbank bleibt unverändert.

Beim Anlegen der ersten Jahresdatei kann die bisherige `verarbeitet.sqlite` als **Stammdatenvorlage** ausgewählt werden. Konten, Rechnungsstellerregeln und vorhandene Einstellungen werden übernommen. Die alte Belegliste wird dabei **nicht übernommen**. Bereits verbuchte Rechnungen daher nicht erneut in den Eingangsordner legen. Der bisherige Verlauf bleibt in der alten Datenbank und kann weiterhin mit Version 2 eingesehen werden.

Für einen normalen Programmwechsel innerhalb Version 3 bleibt die `.belegdb` unverändert erhalten. `lokal.json` im Programmordner behalten, um die zuletzt geöffnete Datei und lokalen Pfade weiterzuverwenden.

## Quellcode und Releases

Der Quellcode enthält vorbereitete GitHub-Workflows für Windows-Tests und ZIP-Releases. Einrichtung und Veröffentlichung sind in `CONTRIBUTING.md` im Quellcodepaket beschrieben. Das Windows-Paket enthält keine persönlichen Belege, Jahresdateien oder Einstellungen.

## Lizenz

BelegLotse steht unter der [GNU General Public License, Version 3](LICENSE) (SPDX: `GPL-3.0-only`). Copyright (c) 2026 Lorenz Uhlig. Nutzung, Änderung und Verkauf sind erlaubt. Bei Weitergabe gelten die GPL-Bedingungen, insbesondere zur Bereitstellung des entsprechenden Quellcodes und zur Lizenzierung abgeleiteter Werke. Das Programm wird ohne Gewährleistung bereitgestellt, soweit gesetzlich zulässig.

Drittrechnungssteller-Komponenten behalten ihre eigenen Lizenzen; siehe [THIRD_PARTY.md](THIRD_PARTY.md).
