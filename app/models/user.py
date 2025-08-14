import mysql.connector
from mysql.connector import Error
from app.config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import logging
import os # <-- IMPORT ADDED

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
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def get(user_id):
        connection = get_db_connection()
        if not connection: return None
        try:
            logger.info(f"Connected to MySQL for user ID {user_id}")
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT id, username, password FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if user:
                    return User(user['id'], user['username'], user['password'])
            return None
        except Error as e:
            logger.error(f"Error fetching user by ID: {e}")
            return None
        finally:
            if connection.is_connected():
                connection.close()

    @staticmethod
    def get_by_username(username):
        connection = get_db_connection()
        if not connection: return None
        try:
            logger.info(f"Connected to MySQL for user {username}")
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                if user:
                    return User(user['id'], user['username'], user['password'])
            return None
        except Error as e:
            logger.error(f"Error fetching user by username: {e}")
            return None
        finally:
            if connection.is_connected():
                connection.close()

    @staticmethod
    def create(username, password):
        connection = get_db_connection()
        if not connection: return False
        try:
            with connection.cursor() as cursor:
                password_hash = generate_password_hash(password)
                cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password_hash))
                connection.commit()
            logger.info(f"User {username} created successfully")
            return True
        except Error as e:
            logger.error(f"Error creating user {username}: {e}")
            return False
        finally:
            if connection.is_connected():
                connection.close()