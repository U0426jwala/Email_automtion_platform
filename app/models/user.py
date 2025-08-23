# app/models/user.py (Corrected)

import mysql.connector
from mysql.connector import Error
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from app.database import get_db_connection  # We are using the central connection
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    # The old get_db_connection staticmethod is deleted, which is correct.

    @staticmethod
    def get(user_id):
        """Retrieve a user by their ID."""
        # THE FIX: Changed User.get_db_connection() to just get_db_connection()
        conn = get_db_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, password_hash FROM users WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            if user_data:
                return User(id=user_data[0], username=user_data[1], password_hash=user_data[2])
            return None
        except Error as e:
            logger.error(f"Error fetching user by ID: {e}")
            return None
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    @staticmethod
    def get_by_username(username):
        """Retrieve a user by their username."""
        # THE FIX: Changed User.get_db_connection() to just get_db_connection()
        conn = get_db_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
            user_data = cursor.fetchone()
            if user_data:
                return User(id=user_data[0], username=user_data[1], password_hash=user_data[2])
            return None
        except Error as e:
            logger.error(f"Error fetching user by username: {e}")
            return None
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    @staticmethod
    def create(username, password):
        """Create a new user with a hashed password."""
        password_hash = generate_password_hash(password)
        # THE FIX: Changed User.get_db_connection() to just get_db_connection()
        conn = get_db_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
            conn.commit()
            user_id = cursor.lastrowid
            return User.get(user_id)
        except Error as e:
            logger.error(f"Error creating user: {e}")
            return None
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()