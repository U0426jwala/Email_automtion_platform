import mysql.connector
from mysql.connector import Error
import os
from app.config import Config
import logging
from datetime import datetime

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

def delete_list_by_id(list_id):
    """
    Deletes a list and all associated contacts in a single transaction.
    """
    connection = get_db_connection()
    if not connection: return False
    try:
        with connection.cursor() as cursor:
            connection.start_transaction()
            
            delete_contacts_query = "DELETE FROM contacts WHERE list_id = %s"
            cursor.execute(delete_contacts_query, (list_id,))
            
            delete_list_query = "DELETE FROM lists WHERE id = %s"
            cursor.execute(delete_list_query, (list_id,))
            
            connection.commit()
            logger.info(f"Successfully deleted list with ID: {list_id} and all its contacts.")
            return True
    except Error as e:
        logger.error(f"Error deleting list ID {list_id}: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if connection and connection.is_connected():
            connection.close()

def create_list(list_name, created_by, total_records=0):
    """Creates a new contact list in the database."""
    connection = get_db_connection()
    if not connection: return None
    try:
        with connection.cursor() as cursor:
            query = "INSERT INTO lists (list_name, created_by, total_records) VALUES (%s, %s, %s)"
            cursor.execute(query, (list_name, created_by, total_records))
            connection.commit()
            list_id = cursor.lastrowid
            logger.info(f"Created new list '{list_name}' with ID: {list_id}")
            return list_id
    except Error as e:
        logger.error(f"Error creating list '{list_name}': {e}")
        return None
    finally:
        if connection and connection.is_connected():
            connection.close()

def save_contact(list_id, name, email, location, company_name, segment=None):
    """Saves a single contact to the database for a specific list."""
    connection = get_db_connection()
    if not connection: return False
    try:
        with connection.cursor() as cursor:
            query = """
            INSERT INTO contacts (list_id, name, email, location, company_name, segment)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (list_id, name, email, location, company_name, segment))
            connection.commit()
            return True
    except Error as e:
        if e.errno == 1062: # Duplicate entry
             logger.warning(f"Contact with email '{email}' already exists in the database.")
        else:
            logger.error(f"Error saving contact {email}: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            connection.close()

def get_lists():
    """Fetches all lists from the database."""
    connection = get_db_connection()
    if not connection: return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
                SELECT l.*, COUNT(c.id) AS total_records 
                FROM lists l
                LEFT JOIN contacts c ON l.id = c.list_id
                GROUP BY l.id
                ORDER BY l.created_at DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Error as e:
        logger.error(f"Error fetching lists: {e}")
        return []
    finally:
        if connection and connection.is_connected():
            connection.close()
            
def get_list_by_id(list_id):
    """Fetches a single list by its ID."""
    connection = get_db_connection()
    if not connection: return None
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM lists WHERE id = %s", (list_id,))
            return cursor.fetchone()
    except Error as e:
        logger.error(f"Error fetching list with ID {list_id}: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()

def get_contacts_for_list(list_id):
    """Fetches all contacts for a given list ID."""
    connection = get_db_connection()
    if not connection: return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = "SELECT id, name, email, location, company_name FROM contacts WHERE list_id = %s ORDER BY name ASC"
            cursor.execute(query, (list_id,))
            return cursor.fetchall()
    except Error as e:
        logger.error(f"Error fetching contacts for list {list_id}: {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()

def update_list_records_count(list_id):
    """Recalculates and updates the total_records count for a specific list."""
    connection = get_db_connection()
    if not connection: return False
    try:
        with connection.cursor() as cursor:
            count_query = "SELECT COUNT(*) FROM contacts WHERE list_id = %s"
            cursor.execute(count_query, (list_id,))
            count = cursor.fetchone()[0]

            update_query = "UPDATE lists SET total_records = %s WHERE id = %s"
            cursor.execute(update_query, (count, list_id))
            connection.commit()
            return True
    except Error as e:
        logger.error(f"Error updating record count for list {list_id}: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()

def delete_contact_by_id(contact_id):
    """Deletes a single contact from the database by their primary key ID."""
    connection = get_db_connection()
    if not connection: return False
    try:
        with connection.cursor() as cursor:
            query = "DELETE FROM contacts WHERE id = %s"
            cursor.execute(query, (contact_id,))
            connection.commit()
            if cursor.rowcount > 0:
                logger.info(f"Successfully deleted contact with ID: {contact_id}")
                return True
            else:
                logger.warning(f"No contact found with ID: {contact_id} to delete.")
                return False
    except Error as e:
        logger.error(f"Error deleting contact ID {contact_id}: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()

# --- MISSING FUNCTIONS ADDED BELOW ---

def get_bounced_emails():
    """Fetches a list of all email addresses from the bounced_emails table."""
    connection = get_db_connection()
    if not connection: return []
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM bounced_emails")
            return [row[0] for row in cursor.fetchall()]
    except Error as e:
        logger.error(f"Error fetching bounced emails: {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()

def get_replied_emails():
    """Fetches a list of all email addresses from the replied_emails table."""
    connection = get_db_connection()
    if not connection: return []
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM replied_emails")
            return [row[0] for row in cursor.fetchall()]
    except Error as e:
        logger.error(f"Error fetching replied emails: {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()