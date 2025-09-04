# app/__init__.py
from flask import Flask
from flask_login import LoginManager
from .config import Config
from .models.user import User
from .celery_app import create_celery_app
import pytz # <-- Import the timezone library

# --- ADD THIS FUNCTION ---


def format_datetime_ist(value, format='%Y-%m-%d %H:%M'):
    """Jinja filter to convert a UTC datetime object from the database back to IST for display."""
    utc_tz = pytz.utc
    local_tz = pytz.timezone('Asia/Kolkata')

    if value.tzinfo is None:
        value = utc_tz.localize(value)

    local_dt = value.astimezone(local_tz)
    return local_dt.strftime(format)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # --- REGISTER THE NEW FILTER WITH THE APP ---
    app.jinja_env.filters['datetime_ist'] = format_datetime_ist

    app.celery = create_celery_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    from .routes.auth_routes import auth_bp
    from .routes.main_routes import main_bp
    from .routes.campaign_routes import campaign_bp
    from .routes.contact_routes import contact_bp
    from .routes.reports_routes import reports_bp
    from .routes.scheduler_routes import scheduler_bp
    from .routes.sequence_routes import sequence_bp
    from .routes.smtp_routes import smtp_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(campaign_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(scheduler_bp)
    app.register_blueprint(sequence_bp)
    app.register_blueprint(smtp_bp)

    return app