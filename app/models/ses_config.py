import mysql.connector
from mysql.connector import Error
import os
import logging
from app.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_db():
    try:
        # Use Config class for database settings
        db_config = {
            'host': Config.MYSQL_HOST,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'database': Config.MYSQL_DB,
            'connection_timeout': 10  # Set timeout to avoid hanging
        }
        if not all(db_config.values()):
            raise ValueError("Missing database configuration parameters")

        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            logger.info("Connected to MySQL database")
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        raise
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()

def save_ses_config(aws_access_key_id, aws_secret_access_key, aws_region, sender_email):
    """
    Save AWS SES configuration to the database.
    SECURITY NOTE: In production, do not store aws_access_key_id and aws_secret_access_key
    in plain text. Use AWS Secrets Manager or encrypt the credentials before storing.
    """
    try:
        # Validate inputs
        if not all([aws_access_key_id, aws_secret_access_key, aws_region, sender_email]):
            raise ValueError("All SES configuration fields are required")

        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            connection_timeout=10
        )
        cursor = connection.cursor()
        query = """
        INSERT INTO ses_configurations (aws_access_key_id, aws_secret_access_key, aws_region, sender_email)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (aws_access_key_id, aws_secret_access_key, aws_region, sender_email))
        connection.commit()
        logger.info("SES configuration saved successfully")
        return True
    except (Error, ValueError) as e:
        logger.error(f"Error saving SES config: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def get_ses_configs():
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            connection_timeout=10
        )
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, aws_region, sender_email, created_at, updated_at FROM ses_configurations")
        configs = cursor.fetchall()
        logger.info("Fetched SES configurations successfully")
        return configs
    except Error as e:
        logger.error(f"Error fetching SES configs: {e}")
        return []
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()