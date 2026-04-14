#!/bin/bash
# Warren Buffett Newsletter - Cronjob Setup
# Speichern unter: /usr/local/bin/send-buffett-newsletter.sh
# Ausführbar machen: chmod +x /usr/local/bin/send-buffett-newsletter.sh

# Cronjob hinzufügen mit: crontab -e
# Für Montag 8 Uhr morgens CET:
# 0 8 * * 1 /usr/local/bin/send-buffett-newsletter.sh >> /var/log/buffett-newsletter.log 2>&1

set -e

# Umgebungsvariablen
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="/home/user/buffett-newsletter"
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="/var/log/buffett-newsletter.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Logging-Funktion
log_message() {
    echo "[$TIMESTAMP] $1" >> $LOG_FILE
}

log_message "🚀 Newsletter-Versand gestartet..."

# Aktiviere Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    log_message "❌ Virtual Environment nicht gefunden unter $VENV_DIR"
    exit 1
fi

source "$VENV_DIR/bin/activate"

# Wechsle zu Projekt-Directory
cd "$PROJECT_DIR"

# Setze Umgebungsvariablen
export FLASK_APP=newsletter_backend.py
export FLASK_ENV=production

# Laden von .env Datei (optional)
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# Führe Python-Skript aus
python << EOF

import sys
from flask import Flask
from newsletter_backend import db, send_weekly_newsletters, app

with app.app_context():
    try:
        log_message("Sending newsletters to all subscribers...")
        send_weekly_newsletters()
        log_message("✓ Newsletter-Versand erfolgreich abgeschlossen!")
    except Exception as e:
        log_message(f"❌ Fehler beim Newsletter-Versand: {str(e)}")
        sys.exit(1)

EOF

# Exit Code prüfen
if [ $? -eq 0 ]; then
    log_message "✓ Cronjob erfolgreich ausgeführt"
else
    log_message "❌ Cronjob mit Fehler beendet"
    exit 1
fi

# Deaktiviere Virtual Environment
deactivate

exit 0
