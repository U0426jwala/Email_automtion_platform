# app/models/smtp_config.py
import mysql.connector
from mysql.connector import Error
from app.database import get_db_connection
from app.config import Config
import os
import logging
from cryptography.fernet import Fernet

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- ENCRYPTION SETUP ---
# Ensure the encryption key is loaded securely from environment variables
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    raise ValueError("No ENCRYPTION_KEY set for Flask application")
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def encrypt_password(password):
    """Encrypts a password using Fernet."""
    if not password:
        return None
    return cipher_suite.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    """Decrypts a password using Fernet."""
    if not encrypted_password:
        return None
    try:
        return cipher_suite.decrypt(encrypted_password.encode()).decode()
    except Exception as e:
        logger.error(f"Failed to decrypt password: {e}")
        return None
# --- END ENCRYPTION SETUP ---



def save_smtp_config(user_id, name, host, port, username, password, use_tls, from_email, from_name):
    """Saves or updates an SMTP configuration for a user."""
    conn = get_db_connection()
    if not conn:
        return False
    
    encrypted_password = encrypt_password(password)

    try:
        cursor = conn.cursor()
        # Using INSERT ... ON DUPLICATE KEY UPDATE for an upsert operation
        # This assumes 'name' and 'user_id' together form a unique key
        query = """
            INSERT INTO smtp_configs (user_id, name, host, port, username, password, use_tls, from_email, from_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                host = VALUES(host),
                port = VALUES(port),
                username = VALUES(username),
                password = VALUES(password),
                use_tls = VALUES(use_tls),
                from_email = VALUES(from_email),
                from_name = VALUES(from_name)
        """
        cursor.execute(query, (user_id, name, host, port, username, encrypted_password, use_tls, from_email, from_name))
        conn.commit()
        return True
    except Error as e:
        logger.error(f"Error saving SMTP config: {e}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_smtp_configs(user_id):
    """Retrieves all SMTP configurations for a user."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, name, host, port, username, use_tls, from_email, from_name FROM smtp_configs WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        configs = cursor.fetchall()
        return configs
    except Error as e:
        logger.error(f"Error fetching SMTP configs for user {user_id}: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_smtp_config_by_id(config_id):
    """Retrieves a single SMTP configuration by its ID, with decrypted password."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM smtp_configs WHERE id = %s"
        cursor.execute(query, (config_id,))
        config = cursor.fetchone()
        if config and config.get('password'):
            config['password'] = decrypt_password(config['password'])
        return config
    except Error as e:
        logger.error(f"Error fetching SMTP config by ID {config_id}: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def delete_smtp_config(config_id, user_id):
    """Deletes an SMTP configuration, ensuring the user has permission."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        # The WHERE clause ensures a user can only delete their own configs
        query = "DELETE FROM smtp_configs WHERE id = %s AND user_id = %s"
        cursor.execute(query, (config_id, user_id))
        conn.commit()
        # cursor.rowcount will be 1 if a row was deleted, 0 otherwise
        return cursor.rowcount > 0
    except Error as e:
        logger.error(f"Error deleting SMTP config {config_id}: {e}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()