# BelegLotse

Eingangsrechnungen lokal aus PDFs erfassen, prüfen, als WISO-TSV exportieren und geordnet ablegen. Die Bedienung erfolgt im Browser, die Verarbeitung auf deinem Windows-Rechner.

**Rechnungen einlesen. Zuordnen. Ablegen.**

## Start unter Windows

1. **Windows-EXE.zip** vollständig in einen beschreibbaren Ordner entpacken.
2. `BelegLotse.exe` doppelklicken. Python und PDF-Bibliotheken sind enthalten.
3. Die App öffnet sich im Standardbrowser. Das Konsolenfenster geöffnet lassen; zum Beenden Strg+C drücken.

Den gesamten Ordner einschließlich `_internal` zusammenlassen. Mehrfachstarts derselben Installation öffnen die laufende App. Die Jahresdatenbank bleibt separat. Beim Update einen neuen Ordner verwenden und die bestehende Jahresdatei in der App öffnen. Optional `lokal.json` aus dem alten Ordner übernehmen, um Startpräferenzen zu behalten.

Das bisherige Windows-ZIP mit `Start.cmd` bleibt als Alternative verfügbar und benötigt Python 3.10+ sowie beim ersten Start Internet zur Einrichtung. OCR benötigt weiterhin eine separate Tesseract-Installation. Die lokale Belegverarbeitung verwendet keinen Cloud-KI-Dienst.

## Version 3.3.1

Eigenständiger EXE-Start und korrigierte Rechnungsstellervorschläge: Maßeinheiten wie „€/kg“ werden nicht mehr mit der Rechtsform „KG“ verwechselt. Bestehende Jahresdateien können weiterverwendet werden.

Unter **„PDF / Regel“** zeigt die App für Rechnungsnummer, Datum und Rechnungssumme die gefundenen Werte mit ihren Beschriftungen. Eine Fundstelle anklicken: **Blau** markiert die Beschriftung, **Gelb** den Wert. Die Vorschau wechselt zur passenden Seite. Mit **„Wert übernehmen“** lässt sich ein Vorschlag in die Prüfliste übernehmen; die Geprüft-Markierung wird dabei aufgehoben. Das Original-PDF bleibt separat zugänglich.

Die Feldhinweise unterscheiden eindeutige Fundstellen, schwächere Vorschläge, Konflikte und fehlende Werte. Alle ausgewählten Belege müssen vor dem Export weiterhin geprüft werden. Ungewöhnliche Layouts, OCR-Fehler und unbeschriftete Werte können eine manuelle Korrektur erfordern. Es gibt keine fest programmierten Sonderfälle für einzelne Rechnungssteller.

### Konten, Steuersätze und Prüfliste

Neue Jahresdateien enthalten 341 EKR03-Konten als bearbeitbare Vorlage. Konten und Steuersätze werden in der Jahresdatei gespeichert; beim Folgejahr können sie aus der bisherigen Datei übernommen werden. Softwareupdates überschreiben sie nicht. Bereits vorhandene Jahresdateien erhalten die Kontenvorlage nicht nachträglich automatisch.

Unter Stammdaten lassen sich Konten suchen, bearbeiten, deaktivieren und aus CSV/TSV importieren (zwei Spalten: Kontonummer, Bezeichnung; optionale Überschrift). Excel-Listen dafür als CSV speichern. Deaktivierte Konten erscheinen nicht mehr in der Vorschlagsliste; bestehende Belegzuordnungen bleiben erhalten.

Steuersatzbezeichnungen sind frei bearbeitbar und erweiterbar. Vorbelegt sind „Keine Vorsteuer“ und „Umsatzsteuer § 13b UStG 19 % o. VSt EU-Untern.“. Der erste Eintrag ist die Vorauswahl. Eine Umbenennung aktualisiert zugeordnete Rechnungssteller und die aktuelle Prüfliste; bereits exportierte Belege bleiben unverändert.

Sachkonto, Geldkonto und Steuersatz können beim Anlegen eines Rechnungsstellers gespeichert werden. In der Prüfliste gelten Änderungen nur für den jeweiligen Beleg. Erst „Als Standard für diesen Rechnungssteller speichern“ übernimmt sie dauerhaft.

„Alle als geprüft markieren“ bestätigt die aktuelle Liste (bereits exportierte Duplikate bleiben ausgeschlossen). „Entfernen“ entfernt nur den Listeneintrag, nicht die Original-PDF. Ein erneuter Scan findet die Datei wieder. Datumseingabe: TT.MM.JJJJ. Fehlermeldungen stehen bei der ausgelösten Aktion; die Kopfzeile im PDF-/Regelfenster bleibt beim Scrollen sichtbar.

Kennungen desselben vorgeschlagenen Rechnungsstellers werden gemeinsam aufgelistet und in einem Schritt bestätigt. Widersprüchliche Firmenzuordnungen bleiben getrennt.

### PDF-Erkennung und Fundstellen

- **Feldzuordnung merken:** Bei einer eindeutigen PDF-Fundstelle „Für zukünftige Belege merken“ wählen. Beschriftung, Rolle, Seite und Position werden beim ausgewählten Rechnungssteller gespeichert, nicht der konkrete Betrag oder die Rechnungsnummer. Passende spätere Vorschläge erhalten den Hinweis „Gemerkte Zuordnung“. Andere Fundstellen, Konflikte und OCR bleiben prüfpflichtig. Gemerkte Zuordnungen lassen sich je Feld löschen. Der gesamte Beleg muss weiterhin als geprüft bestätigt werden.
- **Text auswählen:** In der Vorschau lassen sich Wörter markieren und kopieren. Die Textebene skaliert mit der Zoomstufe und liegt über den Fundstellenmarkierungen. Bei OCR wird die Herkunft angezeigt; der kopierte Text kann Erkennungsfehler enthalten.
- **Rechnungssteller anlegen:** Das Menü einer Belegzeile füllt Name, Merkmale und zuordenbare Kennungen aus dem bereits eingelesenen Beleg vor. Alternativen und Fundstellen können geprüft werden. Erst „Speichern & auswählen“ legt den Rechnungssteller an und wertet den Beleg erneut aus.
- **Sammelzuordnung:** Im Rechnungsstellerstandard „Sammelzuordnung über bestätigte Kennung“ aktivieren, um Belege mit unterschiedlichen Verkäufernamen über eine gemeinsame gespeicherte Kennung zusammenzufassen. Damit dürfen auch Plattformkennungen verwendet werden. Eigene und Empfängerkennungen bleiben ausgeschlossen. Treffen mehrere gespeicherte Rechnungssteller zu, bleibt die Auswahl offen. Die Option ist standardmäßig aus.

Die zuletzt verwendete Jahresdatei wird im Hintergrund geöffnet. Dauert das zu lange, kann dieser Schritt in der Oberfläche übersprungen werden. Die Konsole zeigt Zeiten für Startvorbereitung und Dienststart. Nach einer erfolgreichen Einrichtung wird die vollständige Bibliotheksprüfung nur bei geänderter Umgebung oder nach einem fehlgeschlagenen App-Start wiederholt. Bei einer beschädigten Python-Umgebung kann die Datei `.venv/beleglotse-setup.json` gelöscht und `Start.cmd` erneut gestartet werden.

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

## Darstellung und Pflichtfelder

Oben rechts schaltet das Sonnen-/Mondsymbol zwischen Hell und Dunkel um. Ohne gespeicherte Auswahl startet die App im Dark Mode. Die Auswahl wird auf diesem Rechner gespeichert und bleibt beim Neustart erhalten. Die PDF-Seiten behalten ihre Originaldarstellung.

Fehlende Pflichtfelder ausgewählter Belege werden beim Erstellen der Exportvorschau rot markiert. Die Ansicht springt zum ersten fehlenden Feld; jede Markierung verschwindet, sobald das Feld ausgefüllt ist.

Rechnungen mit 0,00 € werden regulär nummeriert, umbenannt, abgelegt und im Verlauf gespeichert, aber nicht in die TSV geschrieben. Die Vorschau zeigt „Nur Ablage – Betrag 0,00 €“. Enthält die Auswahl nur solche Belege, entsteht keine TSV-Datei. Negative Beträge werden weiterhin exportiert.

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

Diese Bezeichnungen sind Alternativen: Findet die App einen eindeutigen Wert, schlägt sie ihn vor. Mehrere Treffer mit identischem Wert sind unproblematisch. Bei widersprüchlichen gleichwertigen Fundstellen bleibt das Feld zur Klärung leer. Schwächere Alternativen bleiben in der Fundstellenansicht sichtbar.

Die App berücksichtigt Positionen, Zeilen und Spalten. Werte können rechts neben oder direkt unter einer Beschriftung stehen; mehrzeilige und zweisprachige Tabellenköpfe werden berücksichtigt. Alle Seiten werden ausgewertet. Eigene Feldbezeichnungen **ergänzen** die Standardbegriffe. Doppelpunkte und übliche Trennzeichen sind optional. Eine bekannte Datumsbeschriftung wird nicht durch einen Eintrag im Nummernfeld zur Rechnungsnummer.

Rechnungssumme, Netto-/Steuerbeträge und Zahlungsstand werden getrennt bewertet. Ein offener Restbetrag von 0,00 ersetzt die Rechnungssumme nicht. Eine rechnerische Prüfung unterstützt gedruckte Beträge; sie erzeugt keinen erfundenen Rechnungsbetrag. Allgemeine Bezeichnungen wie „Betrag“ sowie vorausbezahlte Summen mit passender Netto-/Steuerrechnung bleiben als prüfpflichtige Vorschläge markiert. Datumsangaben mit Monatsnamen werden unterstützt; bei zweistelligen Jahreszahlen in solchen Angaben wird 2000–2099 angenommen. Das Buchungsjahr ist vor dem Export zu prüfen.


## Rechnungssteller erkennen

### Stammdaten aus Belegen vorschlagen lassen

1. Unter **Einstellungen** eigene USt-IDs und Steuernummern eintragen. Diese Kennungen werden bei der Rechnungsstellererkennung ausgeschlossen. Steuernummern brauchen ein Land, beispielsweise `DE:123/456/78901`.
2. Eingangsordner auswählen und **„Rechnungssteller vorschlagen“** anklicken.
3. Bei einem ausdrücklich beschrifteten Verkäuferbereich schlägt die App dessen Namen als Textmerkmal vor. Andere Belege werden nach verwendbaren Kennungen gruppiert. Soweit im PDF verfügbar, nutzt sie die räumliche Nähe zwischen Kennung und Firmenname. Beispielbelege und Textfundstellen lassen sich direkt öffnen; alternative Namen werden angezeigt.
4. Namen und Kennung anhand des Belegs prüfen. Einen neuen Namen eintragen oder einen vorhandenen Rechnungssteller auswählen. Sachkonto und Geldkonto können gleich ergänzt werden. Bei Steuernummern das Land prüfen beziehungsweise ergänzen.
5. Jeden gewünschten Vorschlag ausdrücklich bestätigen und speichern. **Unbestätigte Vorschläge werden nicht als Stammdaten übernommen.** USt-ID und Steuernummer desselben Unternehmens können nacheinander demselben Rechnungssteller zugeordnet werden.
6. **„Belege mit bestätigten Stammdaten neu einlesen“** anklicken und anschließend die Buchungsangaben prüfen.

Kennungen und Namen sind Vorschläge, keine amtlich geprüften Unternehmensdaten. Auf einer Rechnung können auch Kennungen des Empfängers oder einer Abrechnungsstelle stehen. Eigene sowie ausdrücklich als Empfängerangabe erkannte Kennungen werden ausgeschlossen. Ohne verwendbare Kennung können Firmennamen als prüfpflichtige Vorschläge erscheinen; Kennungen werden dabei nicht erfunden. Belege ohne Vorschläge sowie Lesefehler erscheinen gesondert mit Hinweisen. Für Scans ohne Text wird Tesseract benötigt.

USt-IDs und Steuernummern werden getrennt gespeichert und beim Anlegen eines Folgejahres als Stammdaten übernommen. Eine Kennung kann bei mehreren Rechnungsstellern hinterlegt werden. Für die automatische Zuordnung braucht eine geteilte Kennung ein passendes Namensmerkmal; ohne eindeutige Zuordnung bleibt der Rechnungssteller offen. Deutsche USt-IDs werden auch ohne Feldbezeichnung gesucht; andere Länderformate benötigen eine passende USt-ID-/VAT-Bezeichnung. Die Erkennung deckt nicht jedes internationale Steuerformat ab. Bei Steuernummern ohne eindeutiges Land kann unter Einstellungen ein Standardland angegeben werden.

### Reihenfolge der Zuordnung

Zuerst werden gespeicherte USt-IDs und Steuernummern verglichen; Leerzeichen und übliche Trennzeichen werden vereinheitlicht. **Verwendbare eindeutige Kennungstreffer haben Vorrang vor bloßen Textmerkmalen.** Ausdrücklich erkannte Verkäuferbereiche werden berücksichtigt; reine Plattform-, Empfänger- oder andere Rollenkennungen werden standardmäßig nicht zur Verkäuferzuordnung verwendet. Die ausdrückliche Sammelzuordnung erlaubt zusätzlich Plattformkennungen und unterschiedliche Verkäufernamen. Passen Kennungen mehrerer Rechnungssteller, bleibt die Auswahl offen. Ohne Kennungstreffer greifen die gespeicherten Textregeln:

- **ODER:** Mindestens ein Erkennungsmerkmal muss vorkommen.
- **UND:** Alle Erkennungsmerkmale müssen vorkommen.
- **Ausschlussbegriffe:** Ein gefundener Ausschluss verhindert die automatische Zuordnung zu diesem Rechnungssteller, auch bei einer passenden Kennung.
- Ohne Kennungen und Textmerkmale erfolgt keine automatische Zuordnung. Beim Anlegen wird der Name als editierbarer Textvorschlag vorbelegt. Ohne Merkmale erscheint „Keine automatische Erkennung eingerichtet.“

Textmerkmale werden im PDF-Text gesucht und mit ausdrücklich erkannten Beteiligtenrollen abgeglichen. Ein Name ausschließlich im Empfänger- oder Versanddienstleisterbereich soll keinen Rechnungssteller bestimmen. Rollen ohne erkennbare Beschriftung können unklar bleiben und müssen manuell geprüft werden. Summenbezeichnungen entscheiden nicht über den Rechnungssteller.

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

Text-PDFs werden direkt gelesen. Für Seiten ohne ausreichenden Text lässt sich lokale OCR einschalten. Dafür muss **Tesseract** separat unter Windows installiert sein, mit deutschen oder englischen Sprachdaten. Die App sucht die Installation automatisch; alternativ unter Einstellungen `tesseract.exe` auswählen. OCR bewahrt die Wortpositionen für die Fundstellenansicht. OCR-Werte bleiben als prüfpflichtig markiert. Während einer Sitzung werden die zuletzt gelesenen PDF-Daten im Arbeitsspeicher wiederverwendet; geänderte Dateiinhalte werden neu gelesen.

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
| 6 | Sachkontonummer |
| 7 | Steuersatzbezeichnung |
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

Drittanbieter-Komponenten behalten ihre eigenen Lizenzen; siehe [THIRD_PARTY.md](THIRD_PARTY.md).

Optionaler Oberflächentest: Node.js mit `jsdom` bereitstellen und `python tests/run_ui_masterdata.py` starten. Der Test verwendet ausschließlich temporäre Beispieldaten.
