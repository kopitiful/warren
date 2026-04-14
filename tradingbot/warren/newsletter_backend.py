from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import os
import secrets
from functools import wraps
import requests
import yfinance as yf
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

# --- CONFIGURATION ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///newsletters.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', True)
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'newsletter@buffettpicks.com')

PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
PAYPAL_MODE = os.getenv('PAYPAL_MODE', 'sandbox')  # 'sandbox' or 'live'

db = SQLAlchemy(app)
mail = Mail(app)

# --- DATABASE MODELS ---
class Subscriber(db.Model):
    __tablename__ = 'subscribers'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    tier = db.Column(db.String(20), nullable=False)  # 'free' or 'premium'
    market = db.Column(db.String(10), nullable=False)  # 'us' or 'eu'
    is_confirmed = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    confirmation_token = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    last_newsletter_sent = db.Column(db.DateTime)
    paypal_order_id = db.Column(db.String(100))  # For premium subscribers

class NewsletterLog(db.Model):
    __tablename__ = 'newsletter_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    subscriber_id = db.Column(db.Integer, db.ForeignKey('subscribers.id'), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    market = db.Column(db.String(10))
    top_5_stocks = db.Column(db.JSON)  # JSON array of top 5 stocks
    
    subscriber = db.relationship('Subscriber', backref='newsletters')


# --- EMAIL TEMPLATES ---
def get_confirmation_email(name, confirmation_url):
    return f"""
    <h2>Welcome to Warren Buffett Newsletter!</h2>
    <p>Hi {name},</p>
    <p>Thank you for signing up. Please confirm your email by clicking the link below:</p>
    <p><a href="{confirmation_url}" style="background-color: #378add; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">Confirm Email</a></p>
    <p style="color: #888; font-size: 12px;">Or copy this link: {confirmation_url}</p>
    <p>Best regards,<br>The Warren Buffett Newsletter Team</p>
    """

def get_newsletter_email(name, stocks_html, tier):
    return f"""
    <h2>Weekly Warren Buffett Stock Picks</h2>
    <p>Hi {name},</p>
    <p>Here are this week's top {5 if tier == 'free' else 'analyzed'} stocks based on Warren Buffett's investment criteria:</p>
    {stocks_html}
    <p style="color: #888; font-size: 12px; margin-top: 24px;">
        This newsletter is sent every Monday at 8 AM CET.
        Tier: {tier.upper()}
    </p>
    """


# --- API ENDPOINTS ---

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    """Handle new subscription"""
    data = request.get_json()
    
    if not data.get('email') or not data.get('tier') or not data.get('market'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    email = data.get('email').lower().strip()
    name = data.get('name').strip()
    tier = data.get('tier')
    market = data.get('market')
    
    # Validate tier and market
    if tier not in ['free', 'premium']:
        return jsonify({'error': 'Invalid tier'}), 400
    if market not in ['us', 'eu']:
        return jsonify({'error': 'Invalid market'}), 400
    
    # Check if subscriber already exists
    existing = Subscriber.query.filter_by(email=email).first()
    if existing:
        if existing.is_confirmed:
            return jsonify({'error': 'Email already subscribed'}), 400
        else:
            # Re-send confirmation
            db.session.delete(existing)
            db.session.commit()
    
    # Create new subscriber
    confirmation_token = secrets.token_urlsafe(32)
    subscriber = Subscriber(
        email=email,
        name=name,
        tier=tier,
        market=market,
        confirmation_token=confirmation_token
    )
    
    db.session.add(subscriber)
    db.session.commit()
    
    # Send confirmation email
    confirmation_url = f"{os.getenv('BASE_URL', 'http://localhost:5000')}/confirm/{confirmation_token}"
    
    msg = Message(
        subject='Confirm your Warren Buffett Newsletter subscription',
        recipients=[email],
        html=get_confirmation_email(name, confirmation_url)
    )
    
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Email error: {e}")
        return jsonify({'error': 'Failed to send confirmation email'}), 500
    
    return jsonify({'success': True, 'message': 'Confirmation email sent'}), 201


@app.route('/confirm/<token>', methods=['GET'])
def confirm_email(token):
    """Confirm email and activate subscription"""
    subscriber = Subscriber.query.filter_by(confirmation_token=token).first()
    
    if not subscriber:
        return jsonify({'error': 'Invalid confirmation token'}), 404
    
    subscriber.is_confirmed = True
    subscriber.confirmed_at = datetime.utcnow()
    
    if subscriber.tier == 'free':
        # Activate immediately
        subscriber.is_active = True
        db.session.commit()
        
        # Send welcome email with first newsletter
        send_newsletter_to_subscriber(subscriber)
        
        return jsonify({
            'success': True,
            'message': 'Email confirmed! Your first newsletter will arrive on Monday.',
            'tier': 'free'
        }), 200
    
    elif subscriber.tier == 'premium':
        # Don't activate yet - redirect to PayPal
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Email confirmed. Redirecting to payment...',
            'tier': 'premium',
            'redirect': create_paypal_order(subscriber)
        }), 200


@app.route('/api/paypal/create-order', methods=['POST'])
def paypal_create_order():
    """Create PayPal order"""
    data = request.get_json()
    subscriber_id = data.get('subscriber_id')
    
    subscriber = Subscriber.query.get(subscriber_id)
    if not subscriber:
        return jsonify({'error': 'Subscriber not found'}), 404
    
    try:
        order_id = create_paypal_order_internal(subscriber)
        return jsonify({'orderId': order_id}), 201
    except Exception as e:
        print(f"PayPal error: {e}")
        return jsonify({'error': 'Failed to create order'}), 500


def create_paypal_order_internal(subscriber):
    """Internal PayPal order creation"""
    api_url = f"https://api-m.paypal.com/v2/checkout/orders" if PAYPAL_MODE == 'live' else "https://api-m.sandbox.paypal.com/v2/checkout/orders"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {get_paypal_access_token()}'
    }
    
    payload = {
        'intent': 'CAPTURE',
        'purchase_units': [{
            'amount': {
                'currency_code': 'EUR',
                'value': '9.99'
            },
            'reference_id': str(subscriber.id),
            'description': f'Warren Buffett Newsletter Premium - {subscriber.market.upper()}'
        }],
        'application_context': {
            'brand_name': 'Warren Buffett Newsletter',
            'return_url': f"{os.getenv('BASE_URL', 'http://localhost:5000')}/paypal-success",
            'cancel_url': f"{os.getenv('BASE_URL', 'http://localhost:5000')}/paypal-cancel"
        }
    }
    
    response = requests.post(api_url, json=payload, headers=headers)
    order_data = response.json()
    
    if 'id' in order_data:
        subscriber.paypal_order_id = order_data['id']
        db.session.commit()
        return order_data['id']
    else:
        raise Exception(f"PayPal error: {order_data}")


def get_paypal_access_token():
    """Get PayPal access token"""
    api_url = f"https://api.paypal.com/v1/oauth2/token" if PAYPAL_MODE == 'live' else "https://api.sandbox.paypal.com/v1/oauth2/token"
    
    auth = (PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
    headers = {'Accept': 'application/json', 'Accept-Language': 'en_US'}
    data = {'grant_type': 'client_credentials'}
    
    response = requests.post(api_url, auth=auth, headers=headers, data=data)
    return response.json().get('access_token')


@app.route('/api/paypal/capture-order', methods=['POST'])
def paypal_capture_order():
    """Capture PayPal payment"""
    data = request.get_json()
    order_id = data.get('orderId')
    subscriber_id = data.get('subscriber_id')
    
    subscriber = Subscriber.query.get(subscriber_id)
    if not subscriber or subscriber.paypal_order_id != order_id:
        return jsonify({'error': 'Invalid order'}), 404
    
    try:
        api_url = f"https://api-m.paypal.com/v2/checkout/orders/{order_id}/capture" if PAYPAL_MODE == 'live' else f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {get_paypal_access_token()}'
        }
        
        response = requests.post(api_url, headers=headers)
        capture_data = response.json()
        
        if capture_data.get('status') == 'COMPLETED':
            subscriber.is_active = True
            subscriber.paypal_order_id = order_id
            db.session.commit()
            
            # Send welcome email
            send_premium_welcome_email(subscriber)
            
            return jsonify({'success': True, 'message': 'Payment successful!'}), 200
        else:
            return jsonify({'error': 'Payment failed'}), 400
    
    except Exception as e:
        print(f"Capture error: {e}")
        return jsonify({'error': 'Capture failed'}), 500


@app.route('/api/subscribers/<int:subscriber_id>/unsubscribe', methods=['POST'])
def unsubscribe(subscriber_id):
    """Unsubscribe from newsletter"""
    subscriber = Subscriber.query.get(subscriber_id)
    if not subscriber:
        return jsonify({'error': 'Subscriber not found'}), 404
    
    subscriber.is_active = False
    db.session.commit()
    
    return jsonify({'success': True}), 200


# --- NEWSLETTER LOGIC ---

def analyze_stocks_by_market(market):
    """Analyse stocks using the warren.py logic"""
    ticker_file = f"tickereur.txt" if market == 'eu' else "tickerus.txt"
    
    if not os.path.exists(ticker_file):
        print(f"Ticker file not found: {ticker_file}")
        return []
    
    stocks = []
    
    with open(ticker_file, 'r', encoding='utf-8') as f:
        tickers = sorted(list({
            line.strip().replace('\\', '/').split('/')[-1].upper()
            for line in f if line.strip() and not line.strip().upper().endswith('.TXT')
        }))
    
    for symbol in tickers:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            if not info or 'currentPrice' not in info:
                continue
            
            score = 0
            
            # Burggraben: Marge > 15%
            margin = info.get('profitMargins', 0)
            if margin > 0.15:
                score += 25
            
            # Management: ROE > 15%
            roe = info.get('returnOnEquity', 0)
            if roe > 0.15:
                score += 25
            
            # Cashflow-Qualität: FCF/NetIncome > 0.8
            fcf = info.get('freeCashflow', 0)
            net_inc = info.get('netIncomeToCommon', 1)
            cash_ratio = fcf / net_inc if net_inc != 0 else 0
            if fcf > 0 and cash_ratio > 0.8:
                score += 25
            
            # Sicherheit: Debt/Equity < 80
            de_ratio = info.get('debtToEquity', 999)
            if de_ratio < 80:
                score += 25
            
            if score >= 75:  # Top quality stocks (75%+)
                price = info.get('currentPrice')
                kgv = info.get('forwardPE') or info.get('trailingPE') or 0
                eps = info.get('forwardEps') or info.get('trailingEps', 1)
                
                multiplier = 22 if score == 100 else 15
                fair_value = eps * multiplier
                
                stocks.append({
                    'symbol': symbol,
                    'name': info.get('shortName', symbol)[:18],
                    'industry': info.get('industry', 'N/A')[:22],
                    'score': score,
                    'kgv': round(kgv, 1),
                    'price': round(price, 2),
                    'fair_value': round(fair_value, 2),
                    'upside': round(((fair_value / price) - 1) * 100, 1)
                })
        
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            continue
    
    # Sort by score and upside
    stocks.sort(key=lambda x: (x['score'], x['upside']), reverse=True)
    
    return stocks[:5]  # Return top 5


def generate_stocks_html(stocks):
    """Generate HTML table for stocks"""
    html = '<table style="width: 100%; border-collapse: collapse; margin: 20px 0;">'
    html += '<tr style="background-color: #f5f5f5; border-bottom: 2px solid #378add;">'
    html += '<th style="padding: 10px; text-align: left;">Symbol</th>'
    html += '<th style="padding: 10px; text-align: left;">Score</th>'
    html += '<th style="padding: 10px; text-align: right;">P/E</th>'
    html += '<th style="padding: 10px; text-align: right;">Price</th>'
    html += '<th style="padding: 10px; text-align: right;">Fair Value</th>'
    html += '<th style="padding: 10px; text-align: right;">Upside</th>'
    html += '</tr>'
    
    for stock in stocks:
        html += '<tr style="border-bottom: 1px solid #e0e0e0;">'
        html += f'<td style="padding: 10px;"><strong>{stock["symbol"]}</strong></td>'
        html += f'<td style="padding: 10px;">{stock["score"]}</td>'
        html += f'<td style="padding: 10px; text-align: right;">{stock["kgv"]}</td>'
        html += f'<td style="padding: 10px; text-align: right;">€{stock["price"]}</td>'
        html += f'<td style="padding: 10px; text-align: right;">€{stock["fair_value"]}</td>'
        html += f'<td style="padding: 10px; text-align: right;"><span style="color: #28a745; font-weight: bold;">{stock["upside"]}%</span></td>'
        html += '</tr>'
    
    html += '</table>'
    return html


def send_newsletter_to_subscriber(subscriber):
    """Send newsletter to single subscriber"""
    try:
        stocks = analyze_stocks_by_market(subscriber.market)
        
        if not stocks:
            print(f"No stocks found for {subscriber.market}")
            return False
        
        stocks_html = generate_stocks_html(stocks)
        
        msg = Message(
            subject='Your Warren Buffett Weekly Stock Picks',
            recipients=[subscriber.email],
            html=get_newsletter_email(subscriber.name, stocks_html, subscriber.tier)
        )
        
        mail.send(msg)
        
        # Log newsletter
        log = NewsletterLog(
            subscriber_id=subscriber.id,
            market=subscriber.market,
            top_5_stocks=[s['symbol'] for s in stocks]
        )
        subscriber.last_newsletter_sent = datetime.utcnow()
        
        db.session.add(log)
        db.session.commit()
        
        return True
    
    except Exception as e:
        print(f"Newsletter error: {e}")
        return False


def send_premium_welcome_email(subscriber):
    """Send welcome email to premium subscriber"""
    msg = Message(
        subject='Welcome to Warren Buffett Premium Newsletter',
        recipients=[subscriber.email],
        html=f"""
        <h2>Welcome to Premium!</h2>
        <p>Hi {subscriber.name},</p>
        <p>Thank you for your payment. Your premium subscription is now active.</p>
        <p>You'll receive detailed stock analysis every Monday at 8 AM CET.</p>
        <p>Best regards,<br>The Warren Buffett Newsletter Team</p>
        """
    )
    mail.send(msg)


# --- SCHEDULED JOBS ---

def send_weekly_newsletters():
    """Send newsletters to all active subscribers (Monday 8 AM)"""
    print("Starting weekly newsletter send...")
    
    subscribers = Subscriber.query.filter_by(is_active=True, is_confirmed=True).all()
    
    for subscriber in subscribers:
        send_newsletter_to_subscriber(subscriber)
        print(f"Newsletter sent to {subscriber.email}")
    
    print("Weekly newsletter send completed")


def schedule_newsletter_job():
    """Setup APScheduler for Monday 8 AM CET"""
    scheduler = BackgroundScheduler()
    
    # Every Monday at 8 AM CET
    scheduler.add_job(
        send_weekly_newsletters,
        'cron',
        day_of_week=0,  # Monday
        hour=8,
        minute=0,
        timezone='Europe/Berlin'
    )
    
    scheduler.start()
    print("Newsletter scheduler started")


# --- ADMIN ENDPOINTS ---

@app.route('/admin/stats', methods=['GET'])
def admin_stats():
    """Get subscription statistics"""
    total = Subscriber.query.count()
    confirmed = Subscriber.query.filter_by(is_confirmed=True).count()
    active = Subscriber.query.filter_by(is_active=True).count()
    free = Subscriber.query.filter_by(tier='free').count()
    premium = Subscriber.query.filter_by(tier='premium').count()
    
    return jsonify({
        'total': total,
        'confirmed': confirmed,
        'active': active,
        'free': free,
        'premium': premium
    }), 200


# --- INITIALIZATION ---

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        schedule_newsletter_job()
    
    app.run(debug=True, port=5000)
