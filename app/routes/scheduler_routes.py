# app/routes/scheduler_routes.py

from flask import Blueprint, render_template, flash
from flask_login import login_required
# --- MODIFICATION START ---
# We now import 'get_sequences' from the correct model file
from app.models.sequence import get_sequences
# --- MODIFICATION END ---
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

scheduler_bp = Blueprint('scheduler', __name__)

@scheduler_bp.route('/monitor')
@login_required
def view_scheduled_emails():
    """Renders the monitoring page with a summary of all sequences."""
    try:
        # --- MODIFICATION START ---
        # We now call get_sequences() which provides the necessary data
        sequences_summary = get_sequences()
        # --- MODIFICATION END ---
        return render_template('scheduled_emails_monitor.html', sequences=sequences_summary)
    except Exception as e:
        logger.error(f"Error fetching sequence summary for monitor page: {e}")
        flash("Could not retrieve the sequence summary due to an error.", "danger")
        return render_template('scheduled_emails_monitor.html', sequences=[])