# Warren Buffett Newsletter - Performance Optimization Guide

## 1. Database Indexing

### Current Indexes
```sql
-- Subscriber lookups
CREATE INDEX idx_subscribers_email ON subscribers(email);
CREATE INDEX idx_subscribers_tier ON subscribers(tier);
CREATE INDEX idx_subscribers_market ON subscribers(market);
CREATE INDEX idx_subscribers_is_active ON subscribers(is_active, is_confirmed);

-- Newsletter logs
CREATE INDEX idx_newsletter_logs_subscriber_id ON newsletter_logs(subscriber_id);
CREATE INDEX idx_newsletter_logs_sent_at ON newsletter_logs(sent_at DESC);
CREATE INDEX idx_newsletter_logs_market ON newsletter_logs(market);

-- Combined queries
CREATE INDEX idx_subscribers_active_tier ON subscribers(is_active, tier, market);
```

### Query Optimization
```python
# ❌ BAD: Full table scan
subscribers = Subscriber.query.all()
active = [s for s in subscribers if s.is_active and s.tier == 'premium']

# ✅ GOOD: Use indexes
active = Subscriber.query.filter_by(is_active=True, tier='premium').all()

# ❌ BAD: Multiple queries (N+1 problem)
for subscriber in subscribers:
    logs = NewsletterLog.query.filter_by(subscriber_id=subscriber.id).all()

# ✅ GOOD: Use eager loading
subscribers = Subscriber.query.options(
    db.joinedload(Subscriber.newsletters)
).all()
```

## 2. Caching Strategy

### Redis Setup
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

# Cache subscriber stats (1 hour)
@app.route('/admin/stats')
@cache.cached(timeout=3600)
def admin_stats():
    return jsonify({
        'total': Subscriber.query.count(),
        'confirmed': Subscriber.query.filter_by(is_confirmed=True).count(),
        'active': Subscriber.query.filter_by(is_active=True).count()
    })

# Cache stock analysis (6 hours)
@cache.cached(timeout=21600, key_prefix='stocks_')
def get_top_stocks(market):
    return analyze_stocks_by_market(market)

# Clear cache when subscription changes
@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    # ... subscription logic ...
    cache.delete('admin_stats')
    return response
```

### Cache Key Strategy
```python
# Use subscriber-specific cache for personalized content
cache_key = f'newsletter_{subscriber.id}_{subscriber.market}'

# Use time-based cache keys for time-series data
from datetime import datetime
week_key = f'stocks_{market}_{datetime.now().isocalendar()[1]}'
```

## 3. Query Optimization

### Stock Analysis Performance
```python
# ❌ BAD: Loops with individual API calls
for symbol in tickers:
    stock = yf.Ticker(symbol)
    info = stock.info  # Separate API call per symbol

# ✅ GOOD: Batch processing with caching
import concurrent.futures

def analyze_stocks_batch(tickers, max_workers=4):
    """Analyze multiple stocks in parallel"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(analyze_stock, tickers))
    return [r for r in results if r is not None]

# Even better with caching:
from functools import lru_cache

@lru_cache(maxsize=128)
def analyze_stock_cached(symbol):
    return analyze_stock(symbol)
```

### Newsletter Query Optimization
```python
# ❌ BAD: Multiple queries in loop
results = []
for subscriber in Subscriber.query.filter_by(is_active=True).all():
    stocks = get_top_stocks(subscriber.market)  # Repeated for same market
    results.append((subscriber, stocks))

# ✅ GOOD: Group by market, single analysis per market
from itertools import groupby

active_subs = Subscriber.query.filter_by(is_active=True).all()
by_market = groupby(active_subs, key=lambda s: s.market)

results = []
for market, group in by_market:
    stocks = get_top_stocks(market)  # Once per market
    for subscriber in group:
        results.append((subscriber, stocks))
```

## 4. API Response Optimization

### Pagination
```python
# ❌ BAD: Return all data
@app.route('/admin/subscribers')
def get_subscribers():
    return jsonify(Subscriber.query.all())

# ✅ GOOD: Paginate results
@app.route('/admin/subscribers')
def get_subscribers():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    paginated = Subscriber.query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'items': [s.to_dict() for s in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'page': page
    })
```

### Selective Fields
```python
# ❌ BAD: Return all fields
def subscriber_to_dict(subscriber):
    return {
        'id': subscriber.id,
        'email': subscriber.email,
        'name': subscriber.name,
        'tier': subscriber.tier,
        'market': subscriber.market,
        'is_confirmed': subscriber.is_confirmed,
        'is_active': subscriber.is_active,
        'confirmation_token': subscriber.confirmation_token,  # Sensitive!
        'created_at': subscriber.created_at,
        # ... more fields
    }

# ✅ GOOD: Return only needed fields
def subscriber_to_dict(subscriber, include_token=False):
    data = {
        'id': subscriber.id,
        'email': subscriber.email,
        'name': subscriber.name,
        'tier': subscriber.tier,
        'market': subscriber.market,
        'is_active': subscriber.is_active
    }
    if include_token:
        data['confirmation_token'] = subscriber.confirmation_token
    return data
```

## 5. Email Performance

### Batch Email Sending
```python
# ❌ BAD: Send emails one by one (slow!)
for subscriber in subscribers:
    send_email(subscriber.email, content)

# ✅ GOOD: Use async/celery for email queue
from celery import Celery

celery = Celery(app.name, broker='redis://localhost:6379')

@celery.task
def send_email_async(email, subject, html):
    """Send email asynchronously"""
    msg = Message(subject=subject, recipients=[email], html=html)
    mail.send(msg)

# Queue emails instead of sending directly
for subscriber in subscribers:
    send_email_async.delay(subscriber.email, subject, html)
```

### Connection Pooling
```python
# Configure SMTP connection pooling
app.config['MAIL_POOL'] = True
app.config['MAIL_POOL_SIZE'] = 5
```

## 6. Frontend Performance

### React Optimization
```javascript
// ✅ Use React.memo for signup form component
const SignupForm = React.memo(({ onSubmit }) => {
  // Component only re-renders if props change
  return (/* form JSX */)
});

// ✅ Use useCallback for event handlers
const handleSubmit = useCallback((data) => {
  submitForm(data);
}, [dependencies]);

// ✅ Use Suspense for lazy loading
const AsyncComponent = React.lazy(() => import('./AsyncComponent'));

// ✅ Use useMemo for expensive computations
const memoizedStocks = useMemo(() => {
  return computeTopStocks(allStocks);
}, [allStocks]);
```

### Bundle Optimization
```javascript
// In package.json
{
  "scripts": {
    "build": "react-scripts build",
    "analyze": "source-map-explorer 'build/static/js/*.js'"
  },
  "devDependencies": {
    "source-map-explorer": "^2.5.2"
  }
}

// webpack.config.js code splitting
{
  splitChunks: {
    chunks: 'all',
    cacheGroups: {
      vendor: {
        test: /[\\/]node_modules[\\/]/,
        name: 'vendors',
        priority: 10
      }
    }
  }
}
```

## 7. Database Connection Pooling

### SQLAlchemy Configuration
```python
from sqlalchemy.pool import NullPool, StaticPool, QueuePool

# Development (SQLite)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'check_same_thread': False},
    'poolclass': StaticPool
}

# Production (PostgreSQL)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 20,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 10,
    'pool_timeout': 30
}
```

## 8. Monitoring & Profiling

### Flask-SQLAlchemy Query Profiling
```python
@app.before_request
def before_request():
    from flask import g
    g.db_query_count = 0
    
    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        g.db_query_count += 1
        if g.db_query_count > 50:
            app.logger.warning(f"High query count: {g.db_query_count}")

@app.after_request
def after_request(response):
    if hasattr(g, 'db_query_count'):
        app.logger.info(f"Queries executed: {g.db_query_count}")
    return response
```

### Response Time Monitoring
```python
import time

@app.before_request
def before_request():
    from flask import g
    g.start_time = time.time()

@app.after_request
def after_request(response):
    from flask import g, request
    elapsed = time.time() - g.start_time
    
    if elapsed > 1.0:  # Log slow requests
        app.logger.warning(
            f"Slow request: {request.method} {request.path} "
            f"took {elapsed:.2f}s"
        )
    
    response.headers['X-Response-Time'] = f"{elapsed:.3f}s"
    return response
```

## 9. Deployment Performance Tuning

### Gunicorn Workers
```bash
# Formula: workers = (2 x CPU_cores) + 1
# For quad-core: 9 workers
gunicorn --workers 9 --worker-class sync newsletter_backend:app

# For async tasks:
gunicorn --workers 4 --worker-class gevent --worker-connections 1000
```

### Nginx Caching
```nginx
# Cache static assets
location ~* \.(js|css|png|jpg|jpeg|gif|ico)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# Cache API responses (30 seconds)
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 30s;
    proxy_cache_key "$scheme$request_method$host$request_uri";
}
```

## 10. Performance Checklist

- [ ] Database indexes on frequently queried columns
- [ ] Query optimization (avoid N+1 problems)
- [ ] Redis caching for expensive operations
- [ ] Batch processing for bulk operations
- [ ] Async email sending (Celery)
- [ ] API pagination for large datasets
- [ ] Frontend code splitting and lazy loading
- [ ] Connection pooling configured
- [ ] Response time monitoring
- [ ] Slow query logging
- [ ] CDN for static assets
- [ ] Gzip compression enabled
- [ ] Database replication/backup
- [ ] Load balancing configured

## Benchmarks

### Target Performance Metrics
- API Response Time: < 200ms (95th percentile)
- Newsletter Generation: < 5s for 1000 subscribers
- Stock Analysis: < 2s for 50 stocks
- Email Delivery: < 10s for 100 recipients
- Database Query: < 50ms (95th percentile)

### Load Testing
```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:5000/api/stats

# Using wrk
wrk -t12 -c400 -d30s http://localhost:5000/api/stats

# Using Locust
locust -f locustfile.py --host=http://localhost:5000
```
