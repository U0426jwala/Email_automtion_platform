from flask import Flask
from .config import Config
from .routes.auth_routes import auth_bp
from .routes.ses_routes import ses_bp
from .routes.contact_routes import contact_bp
from .routes.campaign_routes import campaign_bp
from .routes.sequence_routes import sequence_bp
from .routes.main_routes import main_bp
from .routes.scheduler_routes import scheduler_bp
from flask_login import LoginManager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints with their respective URL prefixes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(ses_bp, url_prefix='/ses')
    app.register_blueprint(contact_bp, url_prefix='/contacts')
    app.register_blueprint(campaign_bp, url_prefix='/campaigns')
    app.register_blueprint(sequence_bp, url_prefix='/sequences')
    app.register_blueprint(main_bp)  # No prefix for main routes, keeping at root level
    app.register_blueprint(scheduler_bp, url_prefix='/scheduler')

    from .models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    @app.template_filter('campaign_name')
    def campaign_name_filter(campaign_id, campaigns):
        if campaigns and campaign_id:
            return next((c.get('name') for c in campaigns if c.get('id') == campaign_id), 'N/A')
        return 'N/A'

    return app