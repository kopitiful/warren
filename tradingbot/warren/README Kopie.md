# Warren Buffett Newsletter Platform

Ein minimalistisches Newsletter-System für Warren Buffett Stock-Screening. Das Motto: **Weniger ist mehr**.

## Features

✅ **Einfache Anmeldung** - Free & Premium Tiers  
✅ **Multi-Market** - USA (S&P 500) und Europa (DAX, CAC, AEX)  
✅ **Email Bestätigung** - Automatische Confirmation-Links  
✅ **PayPal Integration** - Sichere Premium-Zahlungen  
✅ **Automatische Newsletter** - Jeden Montag um 8 Uhr morgens  
✅ **Warren Buffett Screening** - Top 5 Aktien mit 75%+ Score  

## Tech Stack

**Backend:**
- Flask (Python Web Framework)
- PostgreSQL (Datenbank)
- yfinance (Stock-Daten)
- APScheduler (Automatische Newsletter)
- Flask-Mail (E-Mail Versand)

**Frontend:**
- React (UI)
- Responsive Design

**Deployment:**
- Docker & Docker Compose (lokale Entwicklung)
- Production-ready mit Gunicorn

## Installation

### Voraussetzungen

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL (oder über Docker)

### 1. Repository klonen

```bash
git clone https://github.com/yourusername/buffett-newsletter.git
cd buffett-newsletter
```

### 2. Environment-Variablen setzen

```bash
cp .env.example .env
```

Bearbeite `.env` mit deinen Credentials:

```env
MAIL_USERNAME=deine-email@gmail.com
MAIL_PASSWORD=dein-app-password
PAYPAL_CLIENT_ID=xxx
PAYPAL_CLIENT_SECRET=xxx
```

### 3. Mit Docker Compose starten

```bash
docker-compose up -d
```

Services werden verfügbar unter:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:5000
- **PostgreSQL:** localhost:5432

### 4. Datenbank initialisieren

```bash
docker-compose exec backend flask db upgrade
```

## API Endpoints

### Subscription

**POST /api/subscribe**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "tier": "free",
  "market": "eu"
}
```

Response:
```json
{
  "success": true,
  "message": "Confirmation email sent"
}
```

**GET /confirm/<token>**
- Bestätigt Email und aktiviert Subscription
- Free-Tier: Newsletter wird sofort nach Bestätigung aktiviert
- Premium-Tier: Leitet zu PayPal weiter

### PayPal

**POST /api/paypal/create-order**
```json
{
  "subscriber_id": 1
}
```

**POST /api/paypal/capture-order**
```json
{
  "orderId": "order-id",
  "subscriber_id": 1
}
```

### Admin

**GET /admin/stats**
```json
{
  "total": 150,
  "confirmed": 120,
  "active": 110,
  "free": 100,
  "premium": 10
}
```

## Email Setup

### Gmail (empfohlen)

1. 2FA aktivieren
2. App-Passwort erstellen: https://myaccount.google.com/apppasswords
3. In `.env` eintragen:
   ```
   MAIL_USERNAME=deine-email@gmail.com
   MAIL_PASSWORD=16-character-app-password
   ```

### Alternatives Email-System

Unterstütze auch andere SMTP-Provider (SendGrid, Mailgun, etc.):

```env
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=SG.xxxxx
```

## PayPal Integration

### Sandbox Setup (Entwicklung)

1. PayPal Developer Account erstellen: https://developer.paypal.com
2. Sandbox-Credentials kopieren
3. In `.env` eintragen:
   ```
   PAYPAL_CLIENT_ID=sandbox-client-id
   PAYPAL_CLIENT_SECRET=sandbox-client-secret
   PAYPAL_MODE=sandbox
   ```

### Live Setup (Produktion)

```env
PAYPAL_MODE=live
PAYPAL_CLIENT_ID=live-client-id
PAYPAL_CLIENT_SECRET=live-client-secret
```

## Newsletter Schedule

**Standard:** Montag 8:00 Uhr CET

Zeitzone in `newsletter_backend.py` anpassen:

```python
scheduler.add_job(
    send_weekly_newsletters,
    'cron',
    day_of_week=0,  # 0=Monday, 1=Tuesday, ...
    hour=8,
    minute=0,
    timezone='Europe/Berlin'  # Ändern wenn nötig
)
```

## Stock-Datenquellen

### European Tickers (`tickereur.txt`)

```
SAP.DE
ASML.AS
LVMH.PA
SIEMENS.DE
ALLIANZ.DE
```

Format: Ein Ticker pro Zeile (yfinance-Format)

### US Tickers (`tickerus.txt`)

```
AAPL
MSFT
JPM
V
JNJ
```

## Deployment

### Heroku

```bash
git push heroku main
heroku run flask db upgrade
heroku config:set MAIL_USERNAME=xxx MAIL_PASSWORD=xxx
```

### AWS / DigitalOcean / Railway

```bash
docker build -f Dockerfile.backend -t buffett-api .
docker run -e DATABASE_URL=... -p 5000:5000 buffett-api
```

### Render / Vercel

Siehe `.github/workflows/deploy.yml`

## Development

### Local Setup ohne Docker

```bash
# Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL=sqlite:///newsletters.db
flask run

# Frontend (neues Terminal)
cd frontend
npm install
npm start
```

### Database Migrations

```bash
flask db init
flask db migrate -m "Add new column"
flask db upgrade
```

### Logging

Logs in `logs/` Verzeichnis:

```bash
tail -f logs/newsletter.log
```

## Testing

```bash
# Unit Tests
pytest tests/

# Integration Tests
pytest tests/ -v --cov

# Load Test
locust -f locustfile.py
```

## Troubleshooting

### Email wird nicht versendet

```
- MAIL_USERNAME/PASSWORD prüfen
- "Weniger sichere Apps" in Gmail aktivieren
- SMTP-Logs checken: docker-compose logs backend
```

### PayPal Error

```
- Sandbox-Mode aktiviert?
- Client-ID/Secret korrekt?
- Firewall blockiert Request?
```

### Newsletter wird nicht gesendet

```
- APScheduler läuft? -> docker-compose logs backend | grep "scheduler"
- Timezone korrekt? -> Prüfe Europe/Berlin
- Test via /api/send-test-newsletter
```

## Security

🔒 **Production Checklist:**

- [ ] `SECRET_KEY` in 50-Zeichen Random String ändern
- [ ] PostgreSQL-Password stärken
- [ ] HTTPS aktivieren (SSL Certificate)
- [ ] Rate Limiting aktivieren
- [ ] CORS auf Frontend-Domain beschränken
- [ ] PayPal Live-Credentials verwenden
- [ ] Email-Provider mit 2FA sichern
- [ ] Database-Backups automatisieren
- [ ] Environment-Variablen in Secrets Manager speichern

## License

MIT License - siehe LICENSE datei

## Support

Fragen? Issues auf GitHub erstellen oder kontaktiere support@buffettpicks.com
