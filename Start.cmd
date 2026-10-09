@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 bootstrap.py
) else (
  python bootstrap.py
)
if errorlevel 1 (
  echo.
  echo Start fehlgeschlagen. Bitte die Fehlermeldung oben beachten.
  echo Voraussetzung: Python 3.10 oder neuer und Internet bei der Ersteinrichtung.
  echo Beim Python-Setup die Option "Add python.exe to PATH" aktivieren.
  pause
)
