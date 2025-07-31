import mysql.connector
from mysql.connector import Error
from app.config import Config
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            connection_timeout=10
        )
    except Error as e:
        logger.error(f"Error establishing database connection: {e}")
        return None

def create_sequence(name, list_id, created_by, status='draft', total_steps=0):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = """
        INSERT INTO sequences (name, list_id, created_by, status, total_steps)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, list_id, created_by, status, total_steps))
        connection.commit()
        sequence_id = cursor.lastrowid
        logger.info(f"Sequence '{name}' created with ID: {sequence_id}")
        return sequence_id
    except Error as e:
        logger.error(f"Error creating sequence '{name}': {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def get_sequences():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT s.*, l.list_name FROM sequences s JOIN lists l ON s.list_id = l.id ORDER BY s.created_at DESC")
        sequences = cursor.fetchall()
        logger.info(f"Fetched {len(sequences)} sequences")
        return sequences
    except Error as e:
        logger.error(f"Error fetching sequences: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def get_sequence(sequence_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT s.*, l.list_name FROM sequences s JOIN lists l ON s.list_id = l.id WHERE s.id = %s", (sequence_id,))
        sequence = cursor.fetchone()
        logger.info(f"Fetched sequence with ID: {sequence_id}")
        return sequence
    except Error as e:
        logger.error(f"Error fetching sequence {sequence_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def update_sequence_status(sequence_id, status):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "UPDATE sequences SET status = %s WHERE id = %s"
        cursor.execute(query, (status, sequence_id))
        connection.commit()
        logger.info(f"Status for sequence {sequence_id} updated to '{status}'")
        return True
    except Error as e:
        logger.error(f"Error updating status for sequence {sequence_id}: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def create_sequence_step(sequence_id, day, campaign_id, schedule_offset_minutes, is_re_reply=False):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = """
        INSERT INTO sequence_steps (sequence_id, day, campaign_id, schedule_offset_minutes, is_re_reply)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (sequence_id, day, campaign_id, schedule_offset_minutes, is_re_reply))
        connection.commit()
        step_id = cursor.lastrowid
        logger.info(f"Sequence step for sequence {sequence_id}, day {day} created with ID: {step_id}")
        return step_id
    except Error as e:
        logger.error(f"Error creating sequence step for sequence {sequence_id}, day {day}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def get_sequence_steps(sequence_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT ss.*, c.name as campaign_name, c.subject as campaign_subject
            FROM sequence_steps ss
            JOIN campaigns c ON ss.campaign_id = c.id
            WHERE ss.sequence_id = %s
            ORDER BY ss.day ASC
        """, (sequence_id,))
        steps = cursor.fetchall()
        return steps
    except Error as e:
        logger.error(f"Error fetching sequence steps for sequence {sequence_id}: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def get_sequence_step(step_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT ss.*, c.name as campaign_name, c.subject as campaign_subject
            FROM sequence_steps ss
            JOIN campaigns c ON ss.campaign_id = c.id
            WHERE ss.id = %s
        """, (step_id,))
        step = cursor.fetchone()
        return step
    except Error as e:
        logger.error(f"Error fetching sequence step {step_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            
def get_sent_emails_for_step(step_id):
    """
    Retrieves a list of contact emails that have already been sent a specific sequence step.
    This is the missing function.
    """
    connection = None
    cursor = None
    sent_to_emails = []
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        # This query assumes a 'sent_emails' table logs each send
        # with an 'email' and 'sequence_step_id'.
        query = "SELECT email FROM sent_emails WHERE sequence_step_id = %s"
        cursor.execute(query, (step_id,))
        results = cursor.fetchall()
        # Create a simple list of email addresses
        sent_to_emails = [item[0] for item in results]
        logger.info(f"Found {len(sent_to_emails)} emails already sent for step ID {step_id}")
    except Error as e:
        logger.error(f"Error fetching sent emails for step {step_id}: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
    return sent_to_emails

def get_latest_sent_log_time(sequence_id):
    """Gets the timestamp of the most recent email sent for a sequence."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "SELECT MAX(sent_at) FROM sent_emails WHERE sequence_id = %s"
        cursor.execute(query, (sequence_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] else None
    except Error as e:
        logger.error(f"Error fetching latest sent log for sequence {sequence_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def update_sequence_step(step_id, day, campaign_id, schedule_offset_minutes, is_re_reply):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = """
        UPDATE sequence_steps
        SET day = %s, campaign_id = %s, schedule_offset_minutes = %s, is_re_reply = %s
        WHERE id = %s
        """
        cursor.execute(query, (day, campaign_id, schedule_offset_minutes, is_re_reply, step_id))
        connection.commit()
        logger.info(f"Sequence step {step_id} updated successfully")
        return True
    except Error as e:
        logger.error(f"Error updating sequence step {step_id}: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def delete_sequence_step(step_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM sequence_steps WHERE id = %s", (step_id,))
        connection.commit()
        logger.info(f"Sequence step {step_id} deleted successfully")
        return True
    except Error as e:
        logger.error(f"Error deleting sequence step {step_id}: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def delete_sequence(sequence_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM sequence_steps WHERE sequence_id = %s", (sequence_id,))
        connection.commit()
        cursor.execute("DELETE FROM sequences WHERE id = %s", (sequence_id,))
        connection.commit()
        logger.info(f"Sequence {sequence_id} and its steps deleted successfully")
        return True
    except Error as e:
        logger.error(f"Error deleting sequence {sequence_id}: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def get_max_day_for_sequence(sequence_id):
    """Gets the highest day number for a given sequence."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "SELECT MAX(day) FROM sequence_steps WHERE sequence_id = %s"
        cursor.execute(query, (sequence_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    except Error as e:
        logger.error(f"Error fetching max day for sequence {sequence_id}: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()