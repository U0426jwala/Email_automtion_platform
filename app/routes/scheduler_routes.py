# scheduler_routes.py

from flask import Blueprint, render_template, flash, jsonify
from flask_login import login_required
from app.models.sequence import get_db_connection # Correctly import the DB helper
from mysql.connector import Error
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

scheduler_bp = Blueprint('scheduler', __name__)

def get_scheduled_sequence_summary():
    """
    Fetches a summary of all sequences for the monitor.
    This function is now self-contained within the routes file.
    """
    connection = get_db_connection()
    if not connection: return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            # This query provides a summary of all sequences and their step counts
            query = """
                SELECT 
                    s.id as sequence_id,
                    s.name as sequence_name,
                    s.status,
                    s.created_at,
                    l.list_name,
                    COUNT(ss.id) as step_count
                FROM sequences s
                JOIN lists l ON s.list_id = l.id
                LEFT JOIN sequence_steps ss ON s.id = ss.sequence_id
                GROUP BY s.id
                ORDER BY s.created_at DESC
            """
            cursor.execute(query)
            summary = cursor.fetchall()
            return summary
    except Error as e:
        logger.error(f"Database error while fetching scheduled sequence summary: {e}")
        return [] # Return an empty list on error
    finally:
        if connection and connection.is_connected():
            connection.close()

@scheduler_bp.route('/monitor')
@login_required
def view_scheduled_emails():
    """Renders the monitoring page with a summary of all sequences."""
    try:
        sequences_summary = get_scheduled_sequence_summary()
        return render_template('scheduled_emails_monitor.html', sequences=sequences_summary)
    except Exception as e:
        logger.error(f"Error fetching sequence summary for monitor page: {e}")
        flash("Could not retrieve the sequence summary due to an error.", "danger")
        return render_template('scheduled_emails_monitor.html', sequences=[])