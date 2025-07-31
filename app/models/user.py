import mysql.connector
from mysql.connector import Error
from app.config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def get(user_id):
        connection = None
        cursor = None
        try:
            connection = mysql.connector.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                connection_timeout=10
            )
            logger.info(f"Connected to MySQL for user ID {user_id}")
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, username, password FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user:
                return User(user['id'], user['username'], user['password'])
            return None
        except Error as e:
            logger.error(f"Error fetching user by ID: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    @staticmethod
    def get_by_username(username):
        connection = None
        cursor = None
        try:
            connection = mysql.connector.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                connection_timeout=10
            )
            logger.info(f"Connected to MySQL for user {username}")
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user:
                return User(user['id'], user['username'], user['password'])
            return None
        except Error as e:
            logger.error(f"Error fetching user by username: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    @staticmethod
    def create(username, password):
        connection = None
        cursor = None
        try:
            connection = mysql.connector.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                connection_timeout=10
            )
            cursor = connection.cursor()
            password_hash = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password_hash))
            connection.commit()
            logger.info(f"User {username} created successfully")
            return True
        except Error as e:
            logger.error(f"Error creating user {username}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()