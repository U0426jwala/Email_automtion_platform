# app/models/reports.py

import mysql.connector
from mysql.connector import Error
from app.database import get_db_connection
from app.config import Config
import os
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



def _get_count(query, params=None):
    """Generic function to execute a COUNT(*) query."""
    conn = get_db_connection()
    if not conn:
        return 0
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        result = cursor.fetchone()
        return result[0] if result else 0
    except Error as e:
        logger.error(f"Error executing count query '{query}': {e}")
        return 0
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_total_sent_count():
    """Gets total number of sent emails."""
    return _get_count("SELECT COUNT(*) FROM sent_emails WHERE status = 'sent'")

def get_total_scheduled_count():
    """Gets total number of scheduled emails."""
    return _get_count("SELECT COUNT(*) FROM sequence_steps WHERE status = 'scheduled'")

def get_total_contacts_count():
    """Gets total number of contacts."""
    return _get_count("SELECT COUNT(*) FROM contacts")

def get_total_lists_count():
    """Gets total number of lists."""
    return _get_count("SELECT COUNT(*) FROM lists")

def get_sent_last_24_hours_count():
    """Gets number of emails sent in the last 24 hours."""
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    query = "SELECT COUNT(*) FROM sent_emails WHERE status = 'sent' AND sent_at >= %s"
    return _get_count(query, (twenty_four_hours_ago,))

def get_sent_monthly_count(year, month):
    """Gets number of emails sent in a specific month and year."""
    query = "SELECT COUNT(*) FROM sent_emails WHERE status = 'sent' AND YEAR(sent_at) = %s AND MONTH(sent_at) = %s"
    return _get_count(query, (year, month))

def get_scheduled_monthly_count(year, month):
    """Gets number of emails scheduled in a specific month and year."""
    query = "SELECT COUNT(*) FROM sequence_steps WHERE status = 'scheduled' AND YEAR(schedule_time) = %s AND MONTH(schedule_time) = %s"
    return _get_count(query, (year, month))

def get_bounced_emails_report():
    """Retrieves a list of bounced emails with contact details."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        # SQL query to join sent_emails with contacts to get the email address and name
        query = """
            SELECT 
                se.sent_at, 
                c.name AS contact_name, 
                c.email AS contact_email, 
                se.subject
            FROM 
                sent_emails se
            JOIN 
                contacts c ON se.contact_id = c.id
            WHERE 
                se.status = 'bounced'
            ORDER BY 
                se.sent_at DESC
        """
        cursor.execute(query)
        bounced_emails = cursor.fetchall()
        return bounced_emails
    except Error as e:
        logger.error(f"Error fetching bounced emails report: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()