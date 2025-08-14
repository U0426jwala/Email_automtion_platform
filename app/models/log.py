import mysql.connector
from mysql.connector import Error
from app.config import Config
import logging
import os

# --- Standard Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Self-Contained Database Connection ---
def get_db_connection():
    """Establishes and returns a database connection."""
    try:
        db_password = os.getenv('MYSQL_PASSWORD')
        
        return mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=db_password,
            database=Config.MYSQL_DB,
            connection_timeout=10
        )
    except Error as e:
        logger.error(f"Error establishing database connection: {e}")
        return None

# --- Main Class Definition ---
class SentEmail:

    @staticmethod
    def log_email(user_id, contact_id, subject, status, campaign_id=None, sequence_id=None, step_id=None, message_id=None):
        """
        Logs a sent email to the database.
        This version is flexible and handles both direct campaign sends and sequence steps.
        """
        connection = get_db_connection()
        if not connection:
            return False

        # The SQL query now includes campaign_id
        query = """
            INSERT INTO sent_emails 
            (user_id, contact_id, campaign_id, sequence_id, step_id, subject, status, message_id, sent_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        try:
            with connection.cursor() as cursor:
                # The parameters in execute() now match the updated query
                cursor.execute(query, (
                    user_id, contact_id, campaign_id, sequence_id, step_id, 
                    subject, status, message_id
                ))
                connection.commit()
                return True
        except Error as e:
            logger.error(f"Database error while logging email for contact {contact_id}: {e}", exc_info=True)
            return False
        finally:
            if connection.is_connected():
                connection.close()

    # --- Statistical Methods (Preserved from your original file) ---

    @staticmethod
    def count_by_user(user_id):
        """Counts all emails sent by a specific user."""
        query = "SELECT COUNT(*) FROM sent_emails WHERE user_id = %s"
        try:
            with get_db_connection() as conn:
                if conn is None: return 0
                with conn.cursor() as cursor:
                    cursor.execute(query, (user_id,))
                    result = cursor.fetchone()
                    return result[0] if result else 0
        except Error as e:
            logger.error(f"Error counting emails by user: {e}")
            return 0

    @staticmethod
    def count_by_user_and_status(user_id, status):
        """Counts emails for a user with a specific status."""
        query = "SELECT COUNT(*) FROM sent_emails WHERE user_id = %s AND status = %s"
        try:
            with get_db_connection() as conn:
                if conn is None: return 0
                with conn.cursor() as cursor:
                    cursor.execute(query, (user_id, status))
                    result = cursor.fetchone()
                    return result[0] if result else 0
        except Error as e:
            logger.error(f"Error counting emails by user and status: {e}")
            return 0

    @staticmethod
    def get_total_sent(user_id):
        """Returns the total number of emails sent by a user."""
        return SentEmail.count_by_user(user_id)

    @staticmethod
    def get_bounced_failed(user_id):
        """Returns the number of bounced/failed emails for a user."""
        bounced = SentEmail.count_by_user_and_status(user_id, 'bounced')
        failed = SentEmail.count_by_user_and_status(user_id, 'failed')
        return bounced + failed
    
    @staticmethod
    def get_successfully_delivered(user_id):
        """Returns the number of successfully delivered emails for a user."""
        return SentEmail.count_by_user_and_status(user_id, 'delivered')