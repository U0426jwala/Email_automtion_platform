# app/models/log.py (Corrected)

from datetime import datetime
import mysql.connector
from mysql.connector import Error
from app.database import get_db_connection
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SentEmail:

    @classmethod
    def log_email(cls, user_id, contact_id, subject, status, campaign_id=None, message_id=None, references=None, sequence_id=None, step_id=None):
        """Logs a sent email attempt in the database."""
        conn = get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO sent_emails (user_id, contact_id, campaign_id, subject, status, sent_at, message_id, `references`, sequence_id, step_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            sent_at = datetime.utcnow()
            cursor.execute(query, (user_id, contact_id, campaign_id, subject, status, sent_at, message_id, references, sequence_id, step_id))
            conn.commit()
            return True
        except Error as e:
            logger.error(f"Error logging sent email: {e}")
            return False
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    @classmethod
    def get_total_sent(cls, user_id):
        """Gets the total number of emails sent by a user."""
        conn = get_db_connection()
        if not conn: return 0
        try:
            cursor = conn.cursor()
            query = "SELECT COUNT(*) FROM sent_emails WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Error as e:
            logger.error(f"Error getting total sent emails: {e}")
            return 0
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    @classmethod
    def get_bounced_failed(cls, user_id):
        """Gets the total number of bounced or failed emails for a user."""
        conn = get_db_connection()
        if not conn: return 0
        try:
            cursor = conn.cursor()
            query = "SELECT COUNT(*) FROM sent_emails WHERE user_id = %s AND (status = 'bounced' OR status = 'failed')"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Error as e:
            logger.error(f"Error getting bounced/failed emails: {e}")
            return 0
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    @classmethod
    def get_successfully_delivered(cls, user_id):
        """Gets the total number of successfully delivered emails (status='sent') for a user."""
        conn = get_db_connection()
        if not conn: return 0
        try:
            cursor = conn.cursor()
            query = "SELECT COUNT(*) FROM sent_emails WHERE user_id = %s AND status = 'sent'"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Error as e:
            logger.error(f"Error getting successfully delivered emails: {e}")
            return 0
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()