# app/models/sequence.py
import mysql.connector
from mysql.connector import Error
from app.database import get_db_connection
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

# --- THIS FUNCTION HAS BEEN FIXED ---
def create_sequence_step(sequence_id, step_number, schedule_time, reply_body, is_re_reply, campaign_id=None):
    """Creates a step within a sequence."""
    conn = get_db_connection()
    if not conn:
        return False

    # FIX 1: Determine the step_type based on the step number.
    step_type = 'email' if step_number == 1 else 'reply'

    try:
        # FIX 2: Validate that an initial step has a campaign ID.
        if step_type == 'email' and campaign_id is None:
            logger.error(f"Cannot create email step for sequence {sequence_id} without a campaign_id.")
            return False
            
        cursor = conn.cursor()
        query = """
            INSERT INTO sequence_steps (sequence_id, step_number, step_type, campaign_id, reply_body, schedule_time, is_re_reply, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'scheduled')
        """
        
        # FIX 3: Pass parameters to the database in the correct order.
        params = (sequence_id, step_number, step_type, campaign_id, reply_body, schedule_time, is_re_reply)
        cursor.execute(query, params)
        
        conn.commit()
        return True
    except Error as e:
        logger.error(f"Database error while creating sequence step: {e}", exc_info=True)
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

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
        query = "SELECT s.*, l.list_name FROM sequences s JOIN lists l ON s.list_id = l.id WHERE s.id = %s;"
        cursor.execute(query, (sequence_id,))
        return cursor.fetchone()
    except Error as e:
        logger.error(f"Database error while getting sequence {sequence_id}: {e}", exc_info=True)
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

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
                COUNT(ss.id) AS total_steps
            FROM sequences s
            JOIN lists l ON s.list_id = l.id
            LEFT JOIN sequence_steps ss ON s.id = ss.sequence_id
            WHERE s.created_by = %s
            GROUP BY s.id ORDER BY s.created_at DESC;
        """
        cursor.execute(query, (user_id,))
        return cursor.fetchall()
    except Error as e:
        logger.error(f"Database error getting sequences for user {user_id}: {e}", exc_info=True)
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_sequence_steps(sequence_id):
    """Fetches all steps for a given sequence, including campaign name."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT ss.*, c.name as campaign_name
            FROM sequence_steps ss
            LEFT JOIN campaigns c ON ss.campaign_id = c.id
            WHERE ss.sequence_id = %s ORDER BY ss.step_number
        """
        cursor.execute(query, (sequence_id,))
        return cursor.fetchall()
    except Error as e:
        logger.error(f"Database error getting steps for sequence {sequence_id}: {e}", exc_info=True)
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_due_steps_for_utc_time(now_utc):
    """
    Fetches all sequence steps that are due based on a provided UTC timestamp.
    This avoids all timezone issues on the database side.
    """
    conn = get_db_connection()
    if not conn:
        logger.warning("Could not establish DB connection to get due steps.")
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                ss.id, ss.sequence_id, ss.campaign_id, ss.reply_body, ss.is_re_reply,
                ss.step_number, s.list_id, s.config_type, s.config_id, s.created_by AS user_id,
                c.subject AS campaign_subject, c.body AS campaign_body
            FROM sequence_steps ss
            JOIN sequences s ON ss.sequence_id = s.id
            LEFT JOIN campaigns c ON ss.campaign_id = c.id
            WHERE ss.status = 'scheduled' 
              AND ss.schedule_time <= %s
              AND s.status = 'active';
        """
        cursor.execute(query, (now_utc,))
        due_steps = cursor.fetchall()
        if due_steps:
            logging.info(f"Found {len(due_steps)} due steps.")
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
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def update_sequence_step(step_id, step_number, campaign_id, reply_body, schedule_time, is_re_reply):
    """Updates the details of a sequence step."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = """
            UPDATE sequence_steps
            SET step_number=%s, campaign_id=%s, reply_body=%s, schedule_time=%s, is_re_reply=%s
            WHERE id=%s
        """
        campaign_id_int = None
        if campaign_id:
            try:
                campaign_id_int = int(campaign_id)
            except (ValueError, TypeError):
                logger.error(f"Invalid campaign_id '{campaign_id}' passed for step {step_id}. It must be a number.")
                return False

        cursor.execute(query, (step_number, campaign_id_int, reply_body, schedule_time, is_re_reply, step_id))
        conn.commit()
        return True
    except Error as e:
        logger.error(f"Error updating sequence step {step_id}: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

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
        if conn and conn.is_connected():
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
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_last_sent_email_for_contact(sequence_id, contact_id):
    """Fetches the most recent sent email to a contact within a specific sequence for threading + quoting."""
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor(dictionary=True) as cursor:
            query = """
                SELECT message_id, `references`, subject, body, from_name, from_email, to_email, sent_at
                FROM sent_emails
                WHERE sequence_id = %s AND contact_id = %s AND status = 'sent'
                ORDER BY sent_at DESC
                LIMIT 1
            """
            cursor.execute(query, (sequence_id, contact_id))
            return cursor.fetchone()
    except Error as e:
        logger.error(f"Error fetching last sent email for contact {contact_id} in sequence {sequence_id}: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            conn.close()

def get_previous_step_subject(sequence_id, current_step_number):
    """Fetches the subject of the step immediately preceding the current one."""
    if current_step_number <= 1:
        return None
    previous_step_number = current_step_number - 1
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.subject
            FROM sequence_steps ss
            JOIN campaigns c ON ss.campaign_id = c.id
            WHERE ss.sequence_id = %s AND ss.step_number = %s
            LIMIT 1;
        """
        cursor.execute(query, (sequence_id, previous_step_number))
        result = cursor.fetchone()
        return result['subject'] if result else "Previous Email Subject"
    except Error as e:
        logger.error(f"Error fetching previous step subject: {e}")
        return "Previous Email Subject"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()