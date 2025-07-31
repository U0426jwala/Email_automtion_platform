import mysql.connector
from mysql.connector import Error
from app.config import Config
import logging

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

def get_scheduled_sequence_summary():
    """
    Fetches a summary of all sequences, including the number of contacts in their list.
    This is used for the redesigned monitor page.
    """
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        # Query to get sequence details and the total number of contacts in the associated list
        query = """
            SELECT 
                s.name as sequence_name,
                s.created_at,
                l.total_records as email_count
            FROM sequences s
            JOIN lists l ON s.list_id = l.id
            WHERE s.status IN ('active', 'finished', 'draft')
            ORDER BY s.created_at DESC
        """
        cursor.execute(query)
        scheduled_summary = cursor.fetchall()
        return scheduled_summary
        
    except Error as e:
        logger.error(f"Database error while fetching scheduled sequence summary: {e}")
        return []
    finally:
        if connection and connection.is_connected():
            if 'cursor' in locals() and cursor:
                cursor.close()
            connection.close()