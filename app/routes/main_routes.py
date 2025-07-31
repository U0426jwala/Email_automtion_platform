from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models.log import SentEmail

# Create a new Blueprint for main application routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/home')
@login_required # Protect this route so only logged-in users can access it
def home():
    """
    Renders the main home page/dashboard.
    Passes the current_user, total_sent, and bounced_failed to the template.
    """
    user_id = current_user.id if current_user.is_authenticated else None
    total_sent = SentEmail.get_total_sent(user_id) if user_id else 0
    bounced_failed = SentEmail.get_bounced_failed(user_id) if user_id else 0
    return render_template('home.html', current_user=current_user, total_sent=total_sent, bounced_failed=bounced_failed)

@main_bp.route('/')
@login_required # Protect the root URL
def index():
    """
    Redirects the base URL ('/') to the home page for logged-in users.
    """
    return redirect(url_for('main.home'))