import mysql.connector
from mysql.connector import Error
from app.config import Config
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Establishes a connection to the MySQL database."""
    try:
        return mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            connection_timeout=10
        )
    except Error as e:
        logger.error(f"Error establishing database connection: {e}")
        return None

class SentEmail:

    @staticmethod
    def count_by_user(user_id):
        conn = get_db_connection()
        if not conn: return 0
        cursor = conn.cursor()
        try:
            # Assuming you have a user_id column in sent_emails table
            cursor.execute("SELECT COUNT(*) FROM sent_emails WHERE user_id = %s", (user_id,))
            count = cursor.fetchone()[0]
        except Error as e:
            logger.error(f"Error counting emails by user: {e}")
            count = 0
        finally:
            cursor.close()
            conn.close()
        return count

    @staticmethod
    def count_by_user_and_status(user_id, status):
        conn = get_db_connection()
        if not conn: return 0
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM sent_emails WHERE user_id = %s AND status = %s", (user_id, status))
            count = cursor.fetchone()[0]
        except Error as e:
            logger.error(f"Error counting emails by user and status: {e}")
            count = 0
        finally:
            cursor.close()
            conn.close()
        return count

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