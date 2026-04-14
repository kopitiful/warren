# Warren Buffett Newsletter - Security Hardening Guide

## 🔒 Security Overview

This document covers critical security measures for protecting user data, payment information, and the platform.

## 1. Authentication & Authorization

### API Key Management
```python
# ❌ BAD: Hardcoded secrets
PAYPAL_SECRET = "secret_key_12345"

# ✅ GOOD: Environment variables with rotation
import os
from dotenv import load_dotenv

load_dotenv()
PAYPAL_SECRET = os.getenv('PAYPAL_SECRET')
# Rotate keys every 90 days
```

### Rate Limiting
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/subscribe', methods=['POST'])
@limiter.limit("5 per minute")  # Strict limit for signup
def subscribe():
    return handle_subscription()

@app.route('/api/stats', methods=['GET'])
@limiter.limit("100 per hour")  # Admin endpoint
def get_stats():
    return jsonify(admin_stats())
```

### CORS Security
```python
from flask_cors import CORS

# ❌ BAD: Allow all origins
CORS(app)

# ✅ GOOD: Whitelist specific origins
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://buffettpicks.com", "https://www.buffettpicks.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
```

## 2. Input Validation & Sanitization

### Form Validation
```python
from wtforms import StringField, SelectField, validators
from wtforms.form import Form

class SubscribeForm(Form):
    email = StringField('email', [
        validators.Email(message='Invalid email'),
        validators.Length(min=5, max=120)
    ])
    name = StringField('name', [
        validators.Length(min=2, max=120),
        validators.Regexp(r'^[a-zA-Z\s\'-]+$', message='Invalid characters')
    ])
    tier = SelectField('tier', choices=[('free', 'Free'), ('premium', 'Premium')])
    market = SelectField('market', choices=[('us', 'US'), ('eu', 'EU')])

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    form = SubscribeForm(request.json)
    if not form.validate():
        return jsonify({'errors': form.errors}), 400
    
    # Process validated data
    return handle_subscription(form.data)
```

### SQL Injection Prevention
```python
# ❌ BAD: String formatting (SQL injection!)
query = f"SELECT * FROM subscribers WHERE email = '{email}'"
db.execute(query)

# ✅ GOOD: Parameterized queries (SQLAlchemy handles this)
subscriber = Subscriber.query.filter_by(email=email).first()

# ✅ GOOD: For raw SQL
from sqlalchemy import text
result = db.session.execute(
    text("SELECT * FROM subscribers WHERE email = :email"),
    {"email": email}
)
```

### XSS Prevention
```python
# ❌ BAD: Unsafe template rendering
<h1>{{ user_input }}</h1>

# ✅ GOOD: Auto-escaped by Jinja2 (default)
<h1>{{ user_input | e }}</h1>

# ✅ GOOD: Explicitly escape in Python
from markupsafe import escape

def send_email(user_input):
    safe_name = escape(user_input)
    html = f"<p>Hello {safe_name}</p>"
    return html
```

## 3. Data Protection

### Password Hashing (if applicable)
```python
from werkzeug.security import generate_password_hash, check_password_hash

# Never store plaintext passwords
password_hash = generate_password_hash('user_password', method='pbkdf2:sha256')

# Verify password
if check_password_hash(password_hash, provided_password):
    # Login successful
    pass
```

### Encryption for Sensitive Data
```python
from cryptography.fernet import Fernet

# Generate key (store securely)
key = Fernet.generate_key()

# Encrypt PayPal order ID
cipher = Fernet(key)
encrypted = cipher.encrypt(b"paypal_order_id")

# Decrypt when needed
decrypted = cipher.decrypt(encrypted)
```

### Data at Rest
```python
# PostgreSQL encryption extension
# Enable in production:
CREATE EXTENSION pgcrypto;

# Encrypt sensitive columns
ALTER TABLE subscribers 
ADD COLUMN email_encrypted bytea;

UPDATE subscribers 
SET email_encrypted = pgp_pub_encrypt(email, keys.pubkey)
FROM keys;
```

## 4. HTTPS & TLS

### SSL Certificate Setup
```bash
# Using Let's Encrypt (automated)
sudo certbot certonly --standalone -d buffettpicks.com -d www.buffettpicks.com

# Auto-renewal (add to crontab)
0 0 1 * * certbot renew --quiet
```

### HSTS Header
```python
@app.after_request
def set_security_headers(response):
    # Force HTTPS for 1 year
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # CSP (Content Security Policy)
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    
    return response
```

## 5. Payment Security

### PayPal Integration
```python
# ✅ GOOD: Verify PayPal webhooks
def verify_paypal_signature(request_body, headers):
    """Verify webhook authenticity"""
    from paypalrestsdk import WebhookEvent
    
    event = WebhookEvent.verify(
        webhook_id=PAYPAL_WEBHOOK_ID,
        event_body=request_body,
        transmission_id=headers['Transmission-Id'],
        transmission_time=headers['Transmission-Time'],
        cert_url=headers['Cert-Url'],
        auth_algo=headers['Auth-Algo'],
        transmission_sig=headers['Transmission-Sig']
    )
    
    return event.valid
```

### PCI Compliance
```python
# ✅ GOOD: Never handle raw card data
# Use PayPal, Stripe, or similar to handle payments
# Never log card numbers or CVV

# ❌ BAD: Storing payment data
order = {
    'card_number': '4111111111111111',  # NEVER!
    'cvv': '123'  # NEVER!
}

# ✅ GOOD: Use tokenization
payment = paypal_api.create_payment(
    amount=9.99,
    currency='EUR',
    token=subscription_token  # Pre-authorized token
)
```

## 6. Database Security

### Database Access Control
```sql
-- Create restricted user
CREATE USER newsletter_app WITH PASSWORD 'strong_password_here';

-- Grant minimal permissions
GRANT CONNECT ON DATABASE buffett_newsletter TO newsletter_app;
GRANT USAGE ON SCHEMA public TO newsletter_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO newsletter_app;

-- Deny DELETE/DROP
REVOKE DELETE, DROP ON ALL TABLES IN SCHEMA public FROM newsletter_app;
```

### Connection Security
```python
# ✅ GOOD: Use SSL connection to PostgreSQL
DATABASE_URL = "postgresql://user:pass@host/db?sslmode=require"

# ✅ GOOD: Connection pooling with timeout
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True  # Test connection before use
)
```

## 7. Logging & Monitoring

### Secure Logging
```python
import logging

# ✅ GOOD: Don't log sensitive data
logger.info(f"User {user_id} subscribed")  # OK
logger.debug(f"Payment token: {paypal_token}")  # BAD!

# Create custom logger that redacts sensitive data
class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        record.msg = self._redact(record.msg)
        return True
    
    def _redact(self, msg):
        import re
        msg = re.sub(r'token["\']?\s*:\s*["\']?[^\s"\']+', 'token: [REDACTED]', msg)
        msg = re.sub(r'email["\']?\s*:\s*["\']?[^\s"\']+', 'email: [REDACTED]', msg)
        return msg

logger.addFilter(SensitiveDataFilter())
```

### Intrusion Detection
```python
# Monitor for suspicious activity
@app.before_request
def check_suspicious_activity():
    from flask import request, g
    
    # Rate limit by IP
    ip = request.remote_addr
    redis_key = f"requests:{ip}"
    
    if redis_client.incr(redis_key) > 100:
        # Too many requests from this IP
        app.logger.warning(f"Suspicious activity from {ip}")
        return {'error': 'Too many requests'}, 429
    
    redis_client.expire(redis_key, 3600)  # 1 hour window
```

## 8. Dependency Management

### Vulnerable Dependency Scanning
```bash
# Check for known vulnerabilities
pip install safety
safety check

# Update dependencies regularly
pip list --outdated
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --upgrade
```

### Requirements with Pinned Versions
```
Flask==2.3.3
SQLAlchemy==2.0.21
yfinance==0.2.32
requests==2.31.0
cryptography==41.0.0
```

## 9. Secrets Management

### Environment Variables Setup
```bash
# ✅ GOOD: Use environment variables
export PAYPAL_CLIENT_ID="sandbox_client_id"
export PAYPAL_CLIENT_SECRET="sandbox_secret"
export MAIL_PASSWORD="app_password"
export SECRET_KEY="random_secure_key"

# ✅ GOOD: Use .env file (never commit!)
# .env
PAYPAL_CLIENT_ID=sandbox_client_id
PAYPAL_CLIENT_SECRET=sandbox_secret

# .gitignore
.env
.env.local
secrets/
```

### AWS Secrets Manager
```python
import boto3

def get_secret(secret_name):
    """Fetch secret from AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='eu-west-1')
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except Exception as e:
        logger.error(f"Error fetching secret: {e}")
        raise
```

## 10. Production Security Checklist

### Before Deployment
- [ ] All API inputs validated
- [ ] HTTPS/TLS enabled with valid certificate
- [ ] Database password changed from default
- [ ] SECRET_KEY randomized (50+ characters)
- [ ] PayPal switched from sandbox to live (if applicable)
- [ ] Email authentication credentials secured
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Security headers set (HSTS, CSP, etc.)
- [ ] Logging enabled (no sensitive data)
- [ ] Error pages don't reveal stack traces
- [ ] Database backups automated
- [ ] Vulnerability scanning tools configured
- [ ] Admin endpoints IP-restricted
- [ ] Dependencies checked for vulnerabilities

### During Operation
- [ ] Monitor application logs for suspicious activity
- [ ] Check failed login attempts
- [ ] Monitor API rate limits
- [ ] Review access logs for unusual patterns
- [ ] Run security updates promptly
- [ ] Rotate API keys every 90 days
- [ ] Test disaster recovery regularly
- [ ] Monitor PayPal/email service health

### Incident Response Plan
1. **Detection**: Monitor logs, alerts, error tracking
2. **Assessment**: Determine scope and impact
3. **Containment**: Block malicious traffic, disable affected accounts
4. **Eradication**: Fix vulnerability, patch systems
5. **Recovery**: Restore from backups if needed
6. **Post-Incident**: Review and improve security

## Security References

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Flask Security: https://flask.palletsprojects.com/security/
- SQLAlchemy Security: https://docs.sqlalchemy.org/security
- PayPal Security: https://developer.paypal.com/docs/checkout/reference/security
- Let's Encrypt: https://letsencrypt.org/
