# app/database.py (Corrected)

import mysql.connector
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from app.config import Config
import os
import logging
from urllib.parse import quote_plus # <-- IMPORT THIS

logger = logging.getLogger(__name__)

try:
    # THE FIX: We now URL-encode the password to handle special characters
    db_password = quote_plus(os.getenv('MYSQL_PASSWORD'))
    
    DATABASE_URI = (
        f"mysql+mysqlconnector://{Config.MYSQL_USER}:{db_password}@"
        f"{Config.MYSQL_HOST}/{Config.MYSQL_DB}?charset=utf8mb4"
    )

    engine = create_engine(
        DATABASE_URI,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600
    )
    logger.info("Database connection pool established successfully.")

except Exception as e:
    logger.critical(f"FATAL ERROR: Could not create database engine. {e}")
    engine = None

def get_db_connection():
    if not engine:
        logger.error("Database engine is not available.")
        return None
    try:
        conn = engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("SET time_zone='+05:30'")
        cursor.close()
        return conn
    except Exception as e:
        logger.error(f"Error getting DB connection from pool: {e}")
        return None