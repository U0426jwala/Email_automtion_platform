from flask import Blueprint, render_template, flash
from flask_login import login_required
# Updated import to reflect the new function name in the model
from app.models.scheduler import get_scheduled_sequence_summary
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

scheduler_bp = Blueprint('scheduler', __name__)

@scheduler_bp.route('/monitor')
@login_required
def view_scheduled_emails():
    """
    Renders the page that displays an aggregated summary of scheduled sequences.
    """
    try:
        # Fetch the aggregated summary data
        sequences_summary = get_scheduled_sequence_summary()
        return render_template('scheduled_emails_monitor.html', sequences=sequences_summary)
    except Exception as e:
        logger.error(f"Error fetching sequence summary for monitoring: {e}")
        flash("Could not retrieve the sequence summary.", "error")
        return render_template('scheduled_emails_monitor.html', sequences=[])