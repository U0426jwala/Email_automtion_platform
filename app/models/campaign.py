import mysql.connector
from mysql.connector import Error
from app.config import Config
import logging
from datetime import datetime
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
def create_campaign(name, subject, body, created_by, status='draft'):
    """Creates a new campaign in the database."""
    connection = get_db_connection()
    if not connection: return None
    try:
        with connection.cursor() as cursor:
            query = """
            INSERT INTO campaigns (name, subject, body, status, created_by)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (name, subject, body, status, created_by))
            connection.commit()
            campaign_id = cursor.lastrowid
        logger.info(f"Campaign '{name}' created with ID: {campaign_id}")
        return campaign_id
    except Error as e:
        logger.error(f"Error creating campaign '{name}': {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()

def get_campaigns():
    """Fetches all campaigns from the database."""
    connection = get_db_connection()
    if not connection: return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT id, name, subject, body, status, created_by, created_at FROM campaigns ORDER BY created_at DESC")
            campaigns = cursor.fetchall()
        logger.info(f"Fetched {len(campaigns)} campaigns")
        return campaigns
    except Error as e:
        logger.error(f"Error fetching campaigns: {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()

def get_campaign(campaign_id):
    """Fetches a single campaign by ID."""
    connection = get_db_connection()
    if not connection: return None
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT id, name, subject, body, status, created_by, created_at FROM campaigns WHERE id = %s", (campaign_id,))
            campaign = cursor.fetchone()
        logger.info(f"Fetched campaign with ID: {campaign_id}")
        return campaign
    except Error as e:
        logger.error(f"Error fetching campaign {campaign_id}: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()

def get_campaign_tags(campaign_id):
    """Fetches tags for a specific campaign."""
    connection = get_db_connection()
    if not connection: return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT tag_name FROM campaign_tags WHERE campaign_id = %s", (campaign_id,))
            tags = [row['tag_name'] for row in cursor.fetchall()]
        logger.info(f"Fetched {len(tags)} tags can campaign ID {campaign_id}")
        return tags
    except Error as e:
        logger.error(f"Error fetching tags for campaign ID {campaign_id}: {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()

def add_campaign_tags(campaign_id, tags):
    """Adds tags to a campaign."""
    connection = get_db_connection()
    if not connection: return False
    try:
        with connection.cursor() as cursor:
            for tag in tags:
                cursor.execute("INSERT INTO campaign_tags (campaign_id, tag_name) VALUES (%s, %s)", (campaign_id, tag))
            connection.commit()
        logger.info(f"Tags added to campaign {campaign_id}")
        return True
    except Error as e:
        logger.error(f"Error adding tags to campaign {campaign_id}: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()

def create_campaign_schedule(campaign_id, scheduled_time, timezone='UTC'):
    """Schedules a campaign for sending."""
    connection = get_db_connection()
    if not connection: return None
    try:
        with connection.cursor() as cursor:
            query = """
            INSERT INTO campaign_schedules (campaign_id, scheduled_time, timezone)
            VALUES (%s, %s, %s)
            """
            cursor.execute(query, (campaign_id, scheduled_time, timezone))
            connection.commit()
            schedule_id = cursor.lastrowid
        logger.info(f"Campaign {campaign_id} scheduled for {scheduled_time} with ID: {schedule_id}")
        return schedule_id
    except Error as e:
        logger.error(f"Error scheduling campaign {campaign_id}: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()