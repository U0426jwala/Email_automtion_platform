# app/__init__.py

from flask import Flask
from flask_login import LoginManager
from .models.user import User
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    # Import and register Blueprints
    from .routes.auth_routes import auth_bp
    from .routes.main_routes import main_bp
    # from .routes.ses_routes import ses_bp  <-- DELETE THIS LINE
    from .routes.contact_routes import contact_bp
    from .routes.campaign_routes import campaign_bp
    from .routes.sequence_routes import sequence_bp
    from .routes.reports_routes import reports_bp
    from .routes.scheduler_routes import scheduler_bp
    from .routes.smtp_routes import smtp_bp 
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    # app.register_blueprint(ses_bp, url_prefix='/ses') <-- DELETE THIS LINE
    app.register_blueprint(contact_bp, url_prefix='/contacts')
    app.register_blueprint(campaign_bp, url_prefix='/campaigns')
    app.register_blueprint(sequence_bp, url_prefix='/sequences')
    app.register_blueprint(reports_bp)
    app.register_blueprint(scheduler_bp, url_prefix='/scheduler')
    app.register_blueprint(smtp_bp, url_prefix='/smtp')
    
    return app