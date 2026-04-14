# Warren Buffett Newsletter - Quick Start Guide

🚀 **5 Minuten bis zur ersten Anmeldung!**

## Schritt 1: Repository klonen

```bash
git clone https://github.com/yourusername/buffett-newsletter.git
cd buffett-newsletter
```

## Schritt 2: .env Datei erstellen

```bash
cp .env.example .env
```

Öffne `.env` und füge deine Credentials ein:

```env
# Gmail (schnellste Option)
MAIL_USERNAME=deine-email@gmail.com
MAIL_PASSWORD=dein-16-stelliges-app-password
MAIL_DEFAULT_SENDER=newsletter@buffettpicks.com

# PayPal Sandbox (zum Testen)
PAYPAL_CLIENT_ID=ARedacted...
PAYPAL_CLIENT_SECRET=EEx...

# Rest ist optional für lokale Entwicklung
```

## Schritt 3: Docker starten

```bash
docker-compose up -d
```

Warte ~30 Sekunden, bis alle Services hochgefahren sind.

Prüfe Status:
```bash
docker-compose ps
```

## Schritt 4: Zugriff

Öffne deinen Browser:

- **Frontend:** http://localhost:3000
- **API:** http://localhost:5000
- **Admins:** http://localhost:5000/admin/stats

Fertig! 🎉

---

## Testen

### 1. Anmeldung testen

```
Frontend öffnen → Free Plan wählen → EUR Market
Email: test@example.com
Name: Test User
```

### 2. Confirmation Email prüfen

```bash
# In MailHog prüfen (lokale Email UI)
# http://localhost:1025
```

### 3. Newsletter manuell senden

```bash
# Terminal:
curl -X POST http://localhost:5000/api/send-test-newsletter \
  -H "Content-Type: application/json" \
  -d '{"market": "eu"}'
```

### 4. PayPal testen

- Im Frontend "Premium" wählen
- Nach Confirmation wird zu PayPal geleitet
- Sandbox-Account: https://sandbox.paypal.com

---

## Häufige Fehler

### ❌ "Confirmation email not sending"

```
1. Prüfe .env Datei (MAIL_USERNAME, MAIL_PASSWORD)
2. Gmail: App-Passwort aktivieren
3. Logs prüfen: docker-compose logs backend
```

### ❌ "Port bereits belegt"

```bash
# Backend Port ändern:
docker-compose.yml -> ports: "5001:5000"

# oder Prozess beenden:
lsof -i :5000
kill -9 <PID>
```

### ❌ "Database connection error"

```bash
# Warte etwas länger
sleep 10
docker-compose up -d

# oder neu starten
docker-compose down
docker-compose up -d
```

---

## Production vorbereiten

Wenn du live gehen möchtest:

1. **Lese DEPLOYMENT.md**
2. **Wähle Host:** Heroku (einfach) oder DigitalOcean (günstig)
3. **Setze reale Credentials:**
   - PayPal Live-Keys (nicht Sandbox!)
   - Email-Provider (Gmail oder SendGrid)
4. **Domain registrieren:** buffettpicks.com
5. **SSL-Zertifikat:** Let's Encrypt (automatisch bei Heroku/Railway)

---

## Nächste Schritte

1. **Ticker-Dateien:** Erstelle `tickereur.txt` und `tickerus.txt` mit deinen Aktien
2. **Customize UI:** Ändere Colors/Logo in `newsletter_frontend.jsx`
3. **Email-Template:** Customize HTML in `newsletter_backend.py`
4. **Add Features:** Premium Content, PDF Reports, etc.

---

## Support

- **Probleme?** → Issues auf GitHub
- **Fragen?** → Schaue README.md oder DEPLOYMENT.md
- **Schnelle Antwort?** → Stack Overflow oder Reddit r/flask

Viel Erfolg! 🚀
