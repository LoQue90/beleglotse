# Entwicklung und Releases

## Lokal testen

Python 3.10 oder neuer verwenden. Abhängigkeiten installieren und Tests starten:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/build_release.py
```

`dist/` enthält das Windows-Startpaket, den Quellcode und SHA-256-Prüfsummen. Das Skript verwendet eine explizite Dateiliste; weder die lokale Python-Umgebung noch Rechnungen, Datenbanken oder Einstellungen gelangen ins Paket. Die Tests benötigen keine privaten Belege. Tesseract ist für die normalen Tests nicht erforderlich.

Das Windows-Paket benötigt weiterhin Python und verwendet `Start.cmd`. Es handelt sich nicht um einen EXE-Build. Der native Ordnerdialog, der Browser-PDF-Viewer und Tesseract sollten zusätzlich auf einem Windows-Rechner geprüft werden.

## Repository einrichten

Den Inhalt des Quellcode-ZIPs (innerhalb des Ordners `beleglotse`) in das Repository übernehmen, einschließlich `.github` und `.gitignore`. Die Dateien `app.py` und `VERSION` liegen dann direkt im Repository-Hauptverzeichnis. Persönliche Dateien nie hinzufügen; `.gitignore` ist bereits vorbereitet.

## Neues Release

Eine Änderung von `VERSION` auf `main` startet ebenfalls automatisch den Release-Workflow. Dieser legt den passenden Tag am geprüften Commit an. Alternativ kann wie unten ein Tag manuell gepusht werden. Bereits vorhandene Tags werden nur akzeptiert, wenn sie auf genau diesen Commit zeigen.

1. `VERSION` aktualisieren und die Änderungen in `CHANGELOG.md` eintragen.
2. Änderungen committen und pushen.
3. Einen Tag in exakt derselben Version erstellen und pushen, beispielsweise:

```sh
git tag v3.0.0
git push origin v3.0.0
```

Der Workflow `Windows release` testet unter `windows-latest`, baut das Paket und hängt folgende Dateien an das GitHub-Release:

- `BelegLotse-v3.0.0-Windows.zip`
- `BelegLotse-v3.0.0-Source.zip`
- `SHA256SUMS.txt`

Das Paket wird nur gebaut, wenn Tag und `VERSION` übereinstimmen. Die Anmeldung erfolgt über das von GitHub bereitgestellte `GITHUB_TOKEN`; kein persönlicher Token ist nötig. Das Repository muss GitHub Actions und Schreibrechte des Release-Jobs für Releases erlauben. Ein erneuter Lauf desselben Tags aktualisiert die angehängten Pakete.

Der Workflow ist vorbereitet, wird aber erst im tatsächlichen GitHub-Repository ausgeführt.

## Lizenz der Beiträge

Beiträge zum eigenen BelegLotse-Code werden unter GPL-3.0-only eingereicht. Drittanbieter-Code muss gesondert gekennzeichnet und lizenzrechtlich kompatibel sein.
