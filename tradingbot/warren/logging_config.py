import logging
import logging.handlers
import os
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easier parsing"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logging(app):
    """Setup application logging"""
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Remove default handler
    app.logger.handlers = []
    
    # File handler - all logs
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = JSONFormatter()
    file_handler.setFormatter(file_formatter)
    app.logger.addHandler(file_handler)
    
    # File handler - errors only
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/error.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    app.logger.addHandler(error_handler)
    
    # File handler - newsletters
    newsletter_handler = logging.handlers.RotatingFileHandler(
        'logs/newsletter.log',
        maxBytes=5242880,  # 5MB
        backupCount=10
    )
    newsletter_handler.setLevel(logging.INFO)
    newsletter_formatter = JSONFormatter()
    newsletter_handler.setFormatter(newsletter_formatter)
    
    newsletter_logger = logging.getLogger('newsletter')
    newsletter_logger.addHandler(newsletter_handler)
    
    # Console handler (development)
    if app.config.get('DEBUG'):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        app.logger.addHandler(console_handler)
    
    # Set log level
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    app.logger.setLevel(getattr(logging, log_level))
    
    return app.logger


class RequestLogger:
    """Log HTTP requests with context"""
    
    def __init__(self, app):
        self.app = app
        
    def setup(self):
        @self.app.before_request
        def before_request():
            from flask import request, g
            g.request_id = request.headers.get('X-Request-ID', 'unknown')
            g.start_time = datetime.utcnow()
        
        @self.app.after_request
        def after_request(response):
            from flask import request, g
            
            duration = (datetime.utcnow() - g.start_time).total_seconds()
            
            self.app.logger.info(
                'HTTP Request',
                extra={
                    'request_id': g.request_id,
                    'method': request.method,
                    'path': request.path,
                    'status': response.status_code,
                    'duration_seconds': duration,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.user_agent.string
                }
            )
            
            return response


# Health check endpoint (for monitoring)
def health_check_endpoint(app):
    @app.route('/health', methods=['GET'])
    def health():
        """Simple health check"""
        return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}, 200


# Email delivery tracking
def log_email_sent(recipient, subject, tier):
    """Log successful email delivery"""
    logger = logging.getLogger('newsletter')
    logger.info(
        f'Email sent to {recipient}',
        extra={
            'recipient': recipient,
            'subject': subject,
            'tier': tier,
            'type': 'email_sent'
        }
    )


def log_email_failed(recipient, subject, error):
    """Log failed email delivery"""
    logger = logging.getLogger('newsletter')
    logger.error(
        f'Email failed for {recipient}: {error}',
        extra={
            'recipient': recipient,
            'subject': subject,
            'error': str(error),
            'type': 'email_failed'
        }
    )


# Newsletter processing
def log_newsletter_sent(subscriber_id, market, stock_count):
    """Log newsletter processing"""
    logger = logging.getLogger('newsletter')
    logger.info(
        f'Newsletter sent to subscriber {subscriber_id}',
        extra={
            'subscriber_id': subscriber_id,
            'market': market,
            'stock_count': stock_count,
            'type': 'newsletter_sent'
        }
    )


# Example integration in newsletter_backend.py:
"""
from logging_config import setup_logging, RequestLogger, log_newsletter_sent

# In your Flask app initialization:
logger = setup_logging(app)
RequestLogger(app).setup()

# When sending newsletter:
try:
    send_newsletter_to_subscriber(subscriber)
    log_newsletter_sent(subscriber.id, subscriber.market, 5)
except Exception as e:
    logger.error(f'Newsletter error: {e}', exc_info=True)
"""
