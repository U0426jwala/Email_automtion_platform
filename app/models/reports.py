# app/models/reports.py

from .sequence import get_db_connection
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_total_sent_count():
    """Counts all successfully sent emails."""
    query = "SELECT COUNT(*) FROM sent_emails WHERE status = 'sent'"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error in get_total_sent_count: {e}")
        return 0

def get_total_scheduled_count():
    """Counts all future scheduled email steps."""
    query = "SELECT COUNT(*) FROM sequence_steps WHERE status = 'scheduled' AND schedule_time > NOW()"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error in get_total_scheduled_count: {e}")
        return 0

def get_total_contacts_count():
    """Counts all contacts in the database."""
    query = "SELECT COUNT(*) FROM contacts"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error in get_total_contacts_count: {e}")
        return 0
        
def get_total_lists_count():
    """Counts all contact lists."""
    query = "SELECT COUNT(*) FROM lists"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error in get_total_lists_count: {e}")
        return 0

def get_sent_last_24_hours_count():
    """Counts emails sent in the last 24 hours."""
    query = "SELECT COUNT(*) FROM sent_emails WHERE status = 'sent' AND sent_at >= NOW() - INTERVAL 1 DAY"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error in get_sent_last_24_hours_count: {e}")
        return 0
    
def get_sent_monthly_count(year, month):
    """Counts successfully sent emails for a specific year and month."""
    query = "SELECT COUNT(*) FROM sent_emails WHERE status = 'sent' AND YEAR(sent_at) = %s AND MONTH(sent_at) = %s"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (year, month))
                return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error in get_sent_monthly_count: {e}")
        return 0

def get_scheduled_monthly_count(year, month):
    """Counts future scheduled emails for a specific year and month."""
    query = "SELECT COUNT(*) FROM sequence_steps WHERE status = 'scheduled' AND YEAR(schedule_time) = %s AND MONTH(schedule_time) = %s"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (year, month))
                return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error in get_scheduled_monthly_count: {e}")
        return 0

def get_bounced_emails_report():
    """Fetches all records from the bounced_emails table for reporting."""
    query = "SELECT email, bounced_at FROM bounced_emails ORDER BY bounced_at DESC"
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query)
                return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error in get_bounced_emails_report: {e}")
        return []