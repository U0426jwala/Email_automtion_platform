# app/models/smtp_config.py
from .user import get_db_connection
from mysql.connector import Error
import logging
import os
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# --- Password Encryption (remains the same) ---
try:
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY').encode()
    cipher_suite = Fernet(ENCRYPTION_KEY)
except Exception as e:
    logger.error("ENCRYPTION_KEY not found or invalid. Please generate one and add it to your .env file.")
    cipher_suite = None

def encrypt_password(password):
    if not cipher_suite or not password: return None
    return cipher_suite.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    if not cipher_suite or not encrypted_password: return None
    return cipher_suite.decrypt(encrypted_password.encode()).decode()

# --- MODIFICATION START: Updated save function ---
def save_smtp_config(user_id, name, host, port, username, password, use_tls, from_email, from_name):
    connection = get_db_connection()
    if not connection: return False
    
    encrypted_pass = encrypt_password(password)
    if not encrypted_pass:
        logger.error("Could not encrypt password. Check ENCRYPTION_KEY.")
        return False

    try:
        with connection.cursor() as cursor:
            query = """
            INSERT INTO smtp_configurations 
                (user_id, name, host, port, username, password, use_tls, from_email, from_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, name, host, port, username, encrypted_pass, use_tls, from_email, from_name))
            connection.commit()
        logger.info(f"SMTP configuration '{name}' saved successfully.")
        return True
    except Error as e:
        logger.error(f"Error saving SMTP config: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()
# --- MODIFICATION END ---

def get_smtp_configs(user_id):
    connection = get_db_connection()
    if not connection: return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = "SELECT id, name, host, port, username, use_tls, from_email, from_name, created_at FROM smtp_configurations WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
    except Error as e:
        logger.error(f"Error fetching SMTP configs: {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()

def get_smtp_config_by_id(config_id):
    connection = get_db_connection()
    if not connection: return None
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = "SELECT * FROM smtp_configurations WHERE id = %s"
            cursor.execute(query, (config_id,))
            config = cursor.fetchone()
            if config and 'password' in config:
                config['password'] = decrypt_password(config['password'])
            return config
    except Error as e:
        logger.error(f"Error fetching SMTP config ID {config_id}: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()

# Add this function to app/models/smtp_config.py

def delete_smtp_config(config_id, user_id):
    """Deletes an SMTP configuration, ensuring the user owns it."""
    connection = get_db_connection()
    if not connection: return False
    
    try:
        with connection.cursor() as cursor:
            # The WHERE clause checks both the config ID and the user ID for security
            query = "DELETE FROM smtp_configurations WHERE id = %s AND user_id = %s"
            cursor.execute(query, (config_id, user_id))
            connection.commit()
            # rowcount will be 1 if a row was deleted, 0 otherwise
            return cursor.rowcount > 0
    except Error as e:
        logger.error(f"Error deleting SMTP config ID {config_id}: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()