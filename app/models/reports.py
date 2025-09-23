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

# --- (All other functions like get_total_sent_count, _get_count, etc. remain unchanged) ---
def _get_count(query, params=None):
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
    return _get_count("SELECT COUNT(*) FROM sent_emails WHERE status = 'sent'")

def get_total_scheduled_count():
    return _get_count("SELECT COUNT(*) FROM sequence_steps WHERE status = 'scheduled' AND schedule_time > UTC_TIMESTAMP()")

def get_total_contacts_count():
    return _get_count("SELECT COUNT(*) FROM contacts")

def get_total_lists_count():
    return _get_count("SELECT COUNT(*) FROM lists")

def get_sent_last_24_hours_count():
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    query = "SELECT COUNT(*) FROM sent_emails WHERE status = 'sent' AND sent_at >= %s"
    return _get_count(query, (twenty_four_hours_ago,))

def get_sent_monthly_count(year, month):
    query = "SELECT COUNT(*) FROM sent_emails WHERE status = 'sent' AND YEAR(sent_at) = %s AND MONTH(sent_at) = %s"
    return _get_count(query, (year, month))

def get_scheduled_monthly_count(year, month):
    query = "SELECT COUNT(*) FROM sequence_steps WHERE status = 'scheduled' AND YEAR(schedule_time) = %s AND MONTH(schedule_time) = %s"
    return _get_count(query, (year, month))

def get_bounced_emails_report():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT se.sent_at, c.name AS contact_name, c.email AS contact_email, se.subject FROM sent_emails se JOIN contacts c ON se.contact_id = c.id WHERE se.status = 'bounced' ORDER BY se.sent_at DESC"
        cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        logger.error(f"Error fetching bounced emails report: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# --- MODIFICATION START: Simplified query to always get totals across all lists ---
def get_future_scheduled_emails_summary():
    """
    Calculates the total number of recipients for each unique future schedule time
    by aggregating data across all sequences and lists.
    """
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        
        # This query first finds each scheduled step, determines the recipient count
        # for the list associated with that step's sequence, and then groups by the
        # exact schedule time to sum up the recipient counts from all sequences
        # firing at that moment.
        query = """
            SELECT
                T.schedule_time,
                SUM(T.recipient_count) AS total_recipients,
                GROUP_CONCAT(DISTINCT T.sequence_name SEPARATOR ', ') AS sequence_names,
                GROUP_CONCAT(DISTINCT T.list_name SEPARATOR ', ') AS list_names
            FROM (
                SELECT
                    ss.schedule_time,
                    s.name AS sequence_name,
                    l.list_name AS list_name,
                    (SELECT COUNT(*) FROM contacts c WHERE c.list_id = s.list_id) AS recipient_count
                FROM
                    sequence_steps ss
                JOIN
                    sequences s ON ss.sequence_id = s.id
                JOIN
                    lists l ON s.list_id = l.id
                WHERE
                    ss.status = 'scheduled' AND ss.schedule_time > UTC_TIMESTAMP()
            ) AS T
            GROUP BY
                T.schedule_time
            ORDER BY
                T.schedule_time ASC;
        """
        cursor.execute(query)
        scheduled_summary = cursor.fetchall()
        return scheduled_summary
    except Error as e:
        logger.error(f"Error fetching future scheduled emails summary with recipient count: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
# --- MODIFICATION END ---

# --- MODIFICATION START: Removed the get_all_list_names_with_sequences function ---
# The function get_all_list_names_with_sequences has been removed as it is no longer needed.
# --- MODIFICATION END ---