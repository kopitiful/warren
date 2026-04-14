# Deployment Guide - Warren Buffett Newsletter

Schritt-für-Schritt Anleitung für Production-Deployment.

## Option 1: Heroku (Einfachste Lösung)

### 1. Heroku CLI installieren
```bash
brew install heroku  # macOS
# oder Windows/Linux: https://devcenter.heroku.com/articles/heroku-cli
```

### 2. Login
```bash
heroku login
```

### 3. App erstellen
```bash
heroku create buffett-newsletter
```

### 4. Umgebungsvariablen setzen
```bash
heroku config:set MAIL_USERNAME=your-email@gmail.com
heroku config:set MAIL_PASSWORD=your-app-password
heroku config:set PAYPAL_CLIENT_ID=xxx
heroku config:set PAYPAL_CLIENT_SECRET=xxx
heroku config:set SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')
```

### 5. PostgreSQL Add-on
```bash
heroku addons:create heroku-postgresql:standard-0
```

### 6. Deploy
```bash
git push heroku main
heroku run flask db upgrade
heroku logs --tail
```

**Kosten:** ~$50-100/Monat (0.5 Dyno + PostgreSQL)

---

## Option 2: Railway (Modern & Günstig)

### 1. Railway CLI installieren
```bash
npm i -g @railway/cli
# oder: brew install railway
```

### 2. Login
```bash
railway login
```

### 3. Neues Projekt
```bash
railway init
```

### 4. Services hinzufügen
```bash
railway add --service postgres
```

### 5. Umgebungsvariablen in Dashboard setzen

### 6. Deploy
```bash
git push railway main
```

**Kosten:** ~$5-30/Monat (Pay-as-you-go)

---

## Option 3: DigitalOcean (App Platform)

### 1. App erstellen
```bash
doctl auth init  # API Token eingeben
doctl apps create --spec app.yaml
```

### 2. `app.yaml` erstellen
```yaml
name: buffett-newsletter
services:
  - name: api
    github:
      repo: username/buffett-newsletter
      branch: main
    build_command: pip install -r requirements.txt
    run_command: gunicorn newsletter_backend:app
    envs:
      - key: DATABASE_URL
        type: POSTGRESQL
      - key: MAIL_USERNAME
        type: SECRET
      - key: MAIL_PASSWORD
        type: SECRET
      - key: PAYPAL_CLIENT_ID
        type: SECRET
      - key: PAYPAL_CLIENT_SECRET
        type: SECRET
  - name: frontend
    github:
      repo: username/buffett-newsletter
      branch: main
    build_command: npm run build
    run_command: npm start

databases:
  - name: postgres
    version: "15"
```

### 3. Deploy
```bash
doctl apps create --spec app.yaml
```

**Kosten:** ~$12-50/Monat

---

## Option 4: AWS (Scalable & Robust)

### 1. RDS PostgreSQL erstellen
```bash
aws rds create-db-instance \
  --db-instance-identifier buffett-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password yourpassword \
  --allocated-storage 20
```

### 2. Elastic Beanstalk App erstellen
```bash
pip install awsebcli
eb init -p python-3.11 buffett-newsletter
eb create buffett-env
```

### 3. .ebextensions/environment.config
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: newsletter_backend:app
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: /var/app/current:$PYTHONPATH
```

### 4. Deploy
```bash
eb deploy
eb setenv MAIL_USERNAME=xxx MAIL_PASSWORD=xxx
```

**Kosten:** ~$15-100/Monat

---

## Production Checklist

### Security
- [ ] `SECRET_KEY` generieren: `python -c 'import secrets; print(secrets.token_urlsafe(50))'`
- [ ] HTTPS aktivieren (Zertifikat von Let's Encrypt)
- [ ] PostgreSQL-Password stark machen (min. 20 Zeichen)
- [ ] Environment-Variablen nicht in Code commiten
- [ ] Firewall: nur Port 80/443 öffentlich

### Database
- [ ] Backups täglich (mindestens 30 Tage aufbewahren)
- [ ] Automated vacuum aktivieren
- [ ] Connections limiten
- [ ] Logging aktivieren

### Monitoring
- [ ] Error Logging (Sentry / Datadog)
- [ ] Uptime Monitoring (UptimeRobot)
- [ ] Email Delivery Monitoring
- [ ] Database Backups überwachen

### Email
- [ ] SPF/DKIM/DMARC Records setzen
- [ ] Unsubscribe-Link in jedem Newsletter
- [ ] Bounce-Handling implementieren
- [ ] Alternative Email-Provider als Backup

### PayPal
- [ ] Live-Credentials verwenden
- [ ] Webhook für Payment-Status implementieren
- [ ] SSL-Zertifikat pinnen
- [ ] IPN Listener aktivieren

---

## Docker Image bauen & pushen

```bash
# Login zu Docker Hub
docker login

# Build
docker build -f Dockerfile.backend -t username/buffett-api:latest .

# Push
docker push username/buffett-api:latest

# Production Run
docker run -e DATABASE_URL=postgresql://... \
  -e MAIL_USERNAME=... \
  -e MAIL_PASSWORD=... \
  -p 80:5000 \
  username/buffett-api:latest
```

---

## Automatische Deploys mit GitHub Actions

`.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
          heroku_app_name: "buffett-newsletter"
          heroku_email: ${{ secrets.HEROKU_EMAIL }}
```

---

## Monitoring & Debugging

### Logs anschauen
```bash
# Heroku
heroku logs --tail

# Railway
railway logs

# DigitalOcean
doctl apps logs get buffett-newsletter

# AWS
eb logs
```

### Error Tracking (Sentry)

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://xxxxx@sentry.io/xxxxx",
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.1
)
```

### Performance Monitoring

```bash
# PostgreSQL Query Logs
SELECT * FROM pg_stat_statements ORDER BY total_time DESC;

# Slow Query Log
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();
```

---

## Häufige Probleme

### Email funktioniert nicht in Production
```
1. SPF Record checken: dig buffettpicks.com TXT
2. DKIM Record aktivieren
3. Gmail App-Passwort erneuern
4. SendGrid / Mailgun als Alternative nutzen
```

### Newsletter wird nicht gesendet
```
1. Cronjob läuft? -> ps aux | grep python
2. APScheduler Timezone korrekt?
3. Test: POST /api/test-newsletter
4. Logs prüfen
```

### PayPal Webhook funktioniert nicht
```
1. Webhook URL öffentlich erreichbar?
2. HTTPS mit gültigem Zertifikat?
3. PayPal Dashboard: Webhook-Logs prüfen
4. Test-Zahlung durchführen
```

---

## Backup & Disaster Recovery

### Automatische Database Backups
```bash
# Heroku
heroku pg:backups:schedule --at '02:00 UTC'

# AWS RDS
aws rds modify-db-instance \
  --db-instance-identifier buffett-db \
  --backup-retention-period 30
```

### Manual Backup
```bash
# Heroku
heroku pg:backups:capture

# PostgreSQL
pg_dump -h host -U user -d database > backup.sql

# Restore
psql -h host -U user -d database < backup.sql
```

---

## Skalierung (wenn nötig)

### Mehr Worker Processes
```bash
# gunicorn config
gunicorn --workers 4 --threads 2 --worker-class=gthread newsletter_backend:app
```

### Redis Caching (optional)
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@app.route('/api/stocks')
@cache.cached(timeout=3600)
def get_stocks():
    ...
```

### Load Balancing
```yaml
# Heroku: Automatic
# DigitalOcean: Load Balancer Service
# AWS: Elastic Load Balancer (ALB)
```

---

## Support & Hilfe

- GitHub Issues: https://github.com/username/buffett-newsletter/issues
- Community: Discord/Slack Channel
- Email: support@buffettpicks.com
- Docs: https://buffett-newsletter.readthedocs.io
