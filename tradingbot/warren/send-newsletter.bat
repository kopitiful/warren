@echo off
REM Warren Buffett Newsletter - Windows Task Scheduler Setup
REM Speichern unter: C:\buffett-newsletter\send-newsletter.bat

setlocal enabledelayedexpansion

REM Umgebungsvariablen
set PROJECT_DIR=C:\buffett-newsletter
set VENV_DIR=%PROJECT_DIR%\venv
set LOG_FILE=%PROJECT_DIR%\logs\newsletter.log
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set TIMESTAMP=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set TIMESTAMP=!TIMESTAMP! %%a:%%b)

if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

REM Logging-Funktion
echo [%TIMESTAMP%] 🚀 Newsletter-Versand gestartet... >> %LOG_FILE%

REM Aktiviere Virtual Environment
if not exist "%VENV_DIR%" (
    echo [%TIMESTAMP%] ❌ Virtual Environment nicht gefunden >> %LOG_FILE%
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"

REM Wechsle zu Projekt-Directory
cd /d "%PROJECT_DIR%"

REM Setze Umgebungsvariablen
set FLASK_APP=newsletter_backend.py
set FLASK_ENV=production

REM Lade .env Datei (PowerShell ist einfacher)
powershell -Command ^
"if (Test-Path '%PROJECT_DIR%\.env') { `
    Get-Content '%PROJECT_DIR%\.env' | ForEach-Object { `
        if ($_ -match '^([^=]+)=(.*)$') { `
            $env:$([System.Text.RegularExpressions.Regex]::Match($_, '^([^=]+)').Value) = $([System.Text.RegularExpressions.Regex]::Match($_, '=(.*)$').Groups[1].Value) `
        } `
    } `
}"

REM Führe Newsletter-Versand aus
python << EOF

import sys
from flask import Flask
from newsletter_backend import db, send_weekly_newsletters, app
import logging
from datetime import datetime

# Setup Logging
logging.basicConfig(
    filename=r'%LOG_FILE%',
    level=logging.INFO,
    format='[%(asctime)s] %(message)s'
)

with app.app_context():
    try:
        logging.info('Sending newsletters to all subscribers...')
        send_weekly_newsletters()
        logging.info('✓ Newsletter-Versand erfolgreich abgeschlossen!')
    except Exception as e:
        logging.error(f'❌ Fehler beim Newsletter-Versand: {str(e)}')
        sys.exit(1)

EOF

if %ERRORLEVEL% equ 0 (
    echo [%TIMESTAMP%] ✓ Cronjob erfolgreich ausgeführt >> %LOG_FILE%
) else (
    echo [%TIMESTAMP%] ❌ Cronjob mit Fehler beendet >> %LOG_FILE%
    exit /b 1
)

REM Deaktiviere Virtual Environment
call "%VENV_DIR%\Scripts\deactivate.bat"

exit /b 0

REM ============================================
REM WINDOWS TASK SCHEDULER SETUP
REM ============================================
REM
REM 1. Öffne Task Scheduler (taskschd.msc)
REM 2. Klick "Create Basic Task"
REM 3. Name: "Warren Buffett Newsletter"
REM 4. Trigger: 
REM    - Wiederholung: Wöchentlich
REM    - Tag: Montag
REM    - Zeit: 08:00 Uhr
REM 5. Action:
REM    - Programm: C:\buffett-newsletter\send-newsletter.bat
REM    - Startdirectory: C:\buffett-newsletter
REM 6. Speichern
REM
REM Alternativ über PowerShell:
REM 
REM $action = New-ScheduledTaskAction -Execute "C:\buffett-newsletter\send-newsletter.bat" -WorkingDirectory "C:\buffett-newsletter"
REM $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "08:00:00"
REM Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "BuffettNewsletter" -Description "Weekly Warren Buffett Newsletter"
REM
