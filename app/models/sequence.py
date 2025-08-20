# app/models/sequence.py

import mysql.connector
from mysql.connector import Error
from app.config import Config
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

# --- MODIFICATION START ---
def create_sequence(name, list_id, created_by, config_type, config_id, status='active'):
    """Creates a new sequence, including its sending configuration."""
    connection = get_db_connection()
    if not connection: return None
    try:
        with connection.cursor() as cursor:
            query = """
            INSERT INTO sequences (name, list_id, created_by, status, config_type, config_id) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (name, list_id, created_by, status, config_type, config_id))
            connection.commit()
            return cursor.lastrowid
    except Error as e:
        logger.error(f"Error creating sequence '{name}': {e}")
        return None
    finally:
        if connection and connection.is_connected():
            connection.close()
# --- MODIFICATION END ---

def create_sequence_step(sequence_id, step_number, type, campaign_id, schedule_time, is_re_reply, status='scheduled'):
    """Creates a new step for a sequence."""
    connection = get_db_connection()
    if not connection: return None
    try:
        with connection.cursor() as cursor:
            query = "INSERT INTO sequence_steps (sequence_id, step_number, type, campaign_id, schedule_time, is_re_reply, status) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (sequence_id, step_number, type, campaign_id, schedule_time, is_re_reply, status))
            connection.commit()
            return cursor.lastrowid
    except Error as e:
        logger.error(f"Error creating step for sequence {sequence_id}: {e}", exc_info=True)
        return None
    finally:
        if connection and connection.is_connected():
            connection.close()

def get_sequences():
    """Fetches all sequences and their step counts for the list view."""
    connection = get_db_connection()
    if not connection: return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            # We also fetch config details to display in the UI
            query = """
                SELECT s.*, l.list_name, COUNT(ss.id) as step_count 
                FROM sequences s 
                LEFT JOIN lists l ON s.list_id = l.id
                LEFT JOIN sequence_steps ss ON s.id = ss.sequence_id
                GROUP BY s.id 
                ORDER BY s.created_at DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Error as e:
        logger.error(f"Error fetching sequences: {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()

def get_sequence(sequence_id):
    """Fetches a single sequence's details, including its sending config."""
    connection = get_db_connection()
    if not connection: return None
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
                SELECT s.*, l.list_name 
                FROM sequences s 
                JOIN lists l ON s.list_id = l.id 
                WHERE s.id = %s
            """
            cursor.execute(query, (sequence_id,))
            return cursor.fetchone()
    except Error as e:
        logger.error(f"Error fetching sequence {sequence_id}: {e}")
        return None
    finally:
        if connection and connection.is_connected():
            connection.close()

def get_sequence_steps(sequence_id):
    """Fetches all steps for a given sequence."""
    connection = get_db_connection()
    if not connection: return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
                SELECT ss.*, c.name as campaign_name
                FROM sequence_steps ss
                JOIN campaigns c ON ss.campaign_id = c.id
                WHERE ss.sequence_id = %s
                ORDER BY ss.step_number ASC
            """
            cursor.execute(query, (sequence_id,))
            return cursor.fetchall()
    except Error as e:
        logger.error(f"Error fetching steps for sequence {sequence_id}: {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()
            
def get_sequence_step(step_id):
    """Fetches a single sequence step by its ID."""
    connection = get_db_connection()
    if not connection: return None
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM sequence_steps WHERE id = %s", (step_id,))
            return cursor.fetchone()
    except Error as e:
        logger.error(f"Error fetching sequence step {step_id}: {e}")
        return None
    finally:
        if connection and connection.is_connected():
            connection.close()

def update_sequence_step(step_id, step_number, type, campaign_id, schedule_time, is_re_reply):
    """Updates an existing sequence step."""
    connection = get_db_connection()
    if not connection: return False
    try:
        with connection.cursor() as cursor:
            query = """
                UPDATE sequence_steps
                SET campaign_id = %s, schedule_time = %s, is_re_reply = %s, status = 'scheduled'
                WHERE id = %s
            """
            cursor.execute(query, (campaign_id, schedule_time, is_re_reply, step_id))
            connection.commit()
            return True
    except Error as e:
        logger.error(f"Error updating sequence step {step_id}: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            connection.close()

# --- MODIFICATION START ---
def get_due_steps():
    """
    Fetches all due steps and now includes the sending configuration (config_type, config_id)
    from the parent sequence.
    """
    connection = get_db_connection()
    if not connection: return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
                SELECT 
                    ss.id, 
                    ss.sequence_id,
                    ss.schedule_time,
                    ss.is_re_reply,
                    s.list_id,
                    s.created_by AS user_id, 
                    s.config_type,
                    s.config_id,
                    c.subject AS campaign_subject,
                    c.body AS campaign_body,
                    c.id AS campaign_id
                FROM sequence_steps ss
                JOIN sequences s ON ss.sequence_id = s.id
                JOIN campaigns c ON ss.campaign_id = c.id
                WHERE ss.status = 'scheduled' AND ss.schedule_time <= NOW()
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching due steps: {e}", exc_info=True)
        return []
    finally:
        if connection and connection.is_connected():
            connection.close()
# --- MODIFICATION END ---
            
def update_step_status(step_id, status):
    """Updates the status of a single sequence step."""
    connection = get_db_connection()
    if not connection: return False
    try:
        with connection.cursor() as cursor:
            query = "UPDATE sequence_steps SET status = %s WHERE id = %s"
            cursor.execute(query, (status, step_id))
            connection.commit()
            return True
    except Error as e:
        logger.error(f"Error updating status for step {step_id}: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()

def delete_sequence_step(step_id):
    """Deletes a single step from a sequence."""
    connection = get_db_connection()
    if not connection: return False
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM sequence_steps WHERE id = %s", (step_id,))
            connection.commit()
            return True
    except Error as e:
        logger.error(f"Error deleting sequence step {step_id}: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()

def delete_sequence(sequence_id):
    """Deletes an entire sequence and all its associated steps."""
    connection = get_db_connection()
    if not connection: return False
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM sequence_steps WHERE sequence_id = %s", (sequence_id,))
            cursor.execute("DELETE FROM sequences WHERE id = %s", (sequence_id,))
            connection.commit()
            return True
    except Error as e:
        logger.error(f"Error deleting sequence {sequence_id}: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()

def get_last_sent_email_for_contact(sequence_id, contact_id):
    """Fetches the most recent sent email to a contact within a specific sequence for threading."""
    connection = get_db_connection()
    if not connection: return None
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
                SELECT se.message_id, se.sent_at, se.subject, c.body AS campaign_body
                FROM sent_emails se
                JOIN sequence_steps ss ON se.step_id = ss.id
                JOIN campaigns c ON ss.campaign_id = c.id
                WHERE se.sequence_id = %s AND se.contact_id = %s AND se.status = 'sent'
                ORDER BY se.sent_at DESC
                LIMIT 1
            """
            cursor.execute(query, (sequence_id, contact_id))
            return cursor.fetchone()
    except Error as e:
        logger.error(f"Error fetching last sent email for contact {contact_id}: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()