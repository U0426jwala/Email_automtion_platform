# app/models/sequence.py
import mysql.connector
from mysql.connector import Error
from app.database import get_db_connection
from app.config import Config
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_sequence(name, list_id, created_by, config_type, config_id, status='active'):
    """Creates a new sequence."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO sequences (name, list_id, created_by, config_type, config_id, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, list_id, created_by, config_type, config_id, status))
        conn.commit()
        sequence_id = cursor.lastrowid
        return sequence_id
    except Error as e:
        logger.error(f"Database error while creating sequence: {e}", exc_info=True)
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def create_sequence_step(sequence_id, step_number, step_type, related_id, schedule_time, is_re_reply=False):
    """Creates a step within a sequence."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO sequence_steps (sequence_id, step_number, step_type, campaign_id, schedule_time, is_re_reply, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'scheduled')
        """
        cursor.execute(query, (sequence_id, step_number, step_type, related_id, schedule_time, is_re_reply))
        conn.commit()
        return True
    except Error as e:
        logger.error(f"Database error while creating sequence step: {e}", exc_info=True)
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# FIX: This function was missing and caused the ImportError. It's needed by the scheduler.
def get_sequences():
    """Fetches a summary of all sequences with their step counts."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                s.id, s.name, s.status, s.created_at, l.list_name,
                COUNT(ss.id) AS total_steps,
                SUM(CASE WHEN ss.status = 'sent' THEN 1 ELSE 0 END) AS sent_steps
            FROM sequences s
            JOIN lists l ON s.list_id = l.id
            LEFT JOIN sequence_steps ss ON s.id = ss.sequence_id
            GROUP BY s.id
            ORDER BY s.created_at DESC;
        """
        cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        logger.error(f"Database error while getting all sequences: {e}", exc_info=True)
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_sequence(sequence_id):
    """Fetches a single sequence by its ID."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT s.*, l.list_name
            FROM sequences s
            JOIN lists l ON s.list_id = l.id
            WHERE s.id = %s;
        """
        cursor.execute(query, (sequence_id,))
        return cursor.fetchone()
    except Error as e:
        logger.error(f"Database error while getting sequence {sequence_id}: {e}", exc_info=True)
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# FIX: This function was incorrectly named 'get_sequences' before, causing a conflict.
# app/models/sequence.py

# ... (all other functions remain the same)

# app/models/sequence.py
# ... (existing imports and functions)

# app/models/sequence.py

# ... (all other imports and functions)

def get_sequences_by_user(user_id):
    """Fetches a summary of all sequences for a specific user, including step counts."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                s.id, s.name, s.status, s.created_at, l.list_name,
                COUNT(ss.id) AS total_steps,
                SUM(CASE WHEN ss.status = 'sent' THEN 1 ELSE 0 END) AS sent_steps
            FROM sequences s
            JOIN lists l ON s.list_id = l.id
            LEFT JOIN sequence_steps ss ON s.id = ss.sequence_id
            WHERE s.created_by = %s
            GROUP BY s.id
            ORDER BY s.created_at DESC;
        """
        cursor.execute(query, (user_id,))
        sequences = cursor.fetchall()
        
        # Log the fetched data for debugging
        logger.info(f"Fetched sequences for user {user_id}: {sequences}")
        
        return sequences
    except Error as e:
        logger.error(f"Database error while getting sequences for user {user_id}: {e}", exc_info=True)
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ... (all other functions remain the same)

def get_sequence_steps(sequence_id):
    """Fetches all steps for a given sequence."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT ss.*, c.name as campaign_name
            FROM sequence_steps ss
            JOIN campaigns c ON ss.campaign_id = c.id
            WHERE ss.sequence_id = %s
            ORDER BY ss.step_number
        """
        cursor.execute(query, (sequence_id,))
        return cursor.fetchall()
    except Error as e:
        logger.error(f"Database error while getting steps for sequence {sequence_id}: {e}", exc_info=True)
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_due_steps():
    """Fetches all sequence steps that are due to be sent."""
    conn = get_db_connection()
    if not conn:
        logger.warning("Could not establish DB connection to get due steps.")
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                ss.id,
                ss.sequence_id,
                ss.campaign_id,
                ss.is_re_reply,
                s.list_id,
                s.config_type,
                s.config_id,
                s.created_by AS user_id,
                c.subject AS campaign_subject,
                c.body AS campaign_body
            FROM sequence_steps ss
            JOIN sequences s ON ss.sequence_id = s.id
            JOIN campaigns c ON ss.campaign_id = c.id
            WHERE ss.status = 'scheduled' AND ss.schedule_time <= NOW() AND s.status = 'active';
        """
        cursor.execute(query)
        due_steps = cursor.fetchall()
        return due_steps
    except Error as e:
        logger.error(f"Database error while fetching due steps: {e}", exc_info=True)
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def update_step_status(step_id, status):
    """Updates the status of a specific sequence step."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = "UPDATE sequence_steps SET status = %s WHERE id = %s"
        cursor.execute(query, (status, step_id))
        conn.commit()
        return True
    except Error as e:
        logger.error(f"Database error updating step {step_id} to status {status}: {e}", exc_info=True)
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_sequence_step(step_id):
    """Fetches a single sequence step by ID."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM sequence_steps WHERE id = %s"
        cursor.execute(query, (step_id,))
        return cursor.fetchone()
    except Error as e:
        logger.error(f"Error fetching sequence step {step_id}: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def update_sequence_step(step_id, step_number, step_type, campaign_id, schedule_time, is_re_reply):
    """Updates the details of a sequence step."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = """
            UPDATE sequence_steps
            SET step_number=%s, step_type=%s, campaign_id=%s, schedule_time=%s, is_re_reply=%s
            WHERE id=%s
        """
        cursor.execute(query, (step_number, step_type, campaign_id, schedule_time, is_re_reply, step_id))
        conn.commit()
        return True
    except Error as e:
        logger.error(f"Error updating sequence step {step_id}: {e}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# app/models/sequence.py
def delete_sequence_step(step_id):
    """Deletes a sequence step."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sequence_steps WHERE id = %s", (step_id,))
        conn.commit()
        return True
    except Error as e:
        logger.error(f"Error deleting sequence step {step_id}: {e}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
def delete_sequence(sequence_id):
    """Deletes a sequence and all its associated steps."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        conn.start_transaction()
        cursor.execute("DELETE FROM sequence_steps WHERE sequence_id = %s", (sequence_id,))
        cursor.execute("DELETE FROM sequences WHERE id = %s", (sequence_id,))
        conn.commit()
        return True
    except Error as e:
        conn.rollback()
        logger.error(f"Error deleting sequence {sequence_id}: {e}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_last_sent_email_for_contact(sequence_id, contact_id):
    """
    Fetches the most recent sent email to a contact within a specific sequence for threading.
    Now also fetches the 'references' header.
    """
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor(dictionary=True) as cursor:
            query = """
                SELECT se.message_id, se.references, se.sent_at, se.subject, c.body AS campaign_body
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
        if conn and conn.is_connected():
            conn.close()