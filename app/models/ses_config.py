import mysql.connector
from mysql.connector import Error
import os # <-- IMPORT ADDED
import logging
from app.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CORRECTED DATABASE CONNECTION ---
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

# --- NOTE: All direct connection calls below are replaced by get_db_connection() ---
def init_db():
    try:
        connection = get_db_connection()
        if connection and connection.is_connected():
            logger.info("Connected to MySQL database")
            connection.close()
        else:
             raise ValueError("Failed to connect to database.")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise

def save_ses_config(aws_access_key_id, aws_secret_access_key, aws_region, sender_email):
    """
    Save AWS SES configuration to the database.
    SECURITY NOTE: In production, do not store aws_access_key_id and aws_secret_access_key
    in plain text. Use AWS Secrets Manager or encrypt the credentials before storing.
    """
    if not all([aws_access_key_id, aws_secret_access_key, aws_region, sender_email]):
        logger.error("All SES configuration fields are required")
        return False
        
    connection = get_db_connection()
    if not connection: return False
    try:
        with connection.cursor() as cursor:
            query = """
            INSERT INTO ses_configurations (aws_access_key_id, aws_secret_access_key, aws_region, sender_email)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (aws_access_key_id, aws_secret_access_key, aws_region, sender_email))
            connection.commit()
        logger.info("SES configuration saved successfully")
        return True
    except Error as e:
        logger.error(f"Error saving SES config: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()

def get_ses_configs():
    connection = get_db_connection()
    if not connection: return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT id, aws_region, sender_email, created_at, updated_at FROM ses_configurations")
            configs = cursor.fetchall()
        logger.info("Fetched SES configurations successfully")
        return configs
    except Error as e:
        logger.error(f"Error fetching SES configs: {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()