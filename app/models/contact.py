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

def create_list(list_name, created_by, total_records=0, list_type='People'):
    """Creates a new list entry in the database."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = """
        INSERT INTO lists (list_name, total_records, list_type, created_by)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (list_name, total_records, list_type, created_by))
        connection.commit()
        list_id = cursor.lastrowid
        logger.info(f"List '{list_name}' created with ID: {list_id}")
        return list_id
    except Error as e:
        logger.error(f"Error creating list '{list_name}': {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def save_contact(list_id, name, email, location, company_name, segment=None):
    """Saves a single contact to the database."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = """
        INSERT INTO contacts (list_id, name, email, location, company_name, segment)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name), location = VALUES(location), company_name = VALUES(company_name), segment = VALUES(segment)
        """
        cursor.execute(query, (list_id, name, email, location, company_name, segment))
        connection.commit()
        logger.info(f"Contact '{email}' saved/updated successfully for list {list_id}")
        return True
    except Error as e:
        logger.error(f"Error saving contact '{email}': {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def get_lists():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM lists ORDER BY created_at DESC")
        lists = cursor.fetchall()
        logger.info(f"Fetched {len(lists)} lists")
        return lists
    except Error as e:
        logger.error(f"Error fetching lists: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def get_contacts_by_list(list_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM contacts WHERE list_id = %s", (list_id,))
        return cursor.fetchall()
    except Error as e:
        logger.error(f"Error fetching contacts for list {list_id}: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def update_list_records_count(list_id, count):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE lists SET total_records = %s WHERE id = %s", (count, list_id))
        connection.commit()
        logger.info(f"Updated total_records for list {list_id} to {count}")
        return True
    except Error as e:
        logger.error(f"Error updating total_records for list {list_id}: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def get_bounced_emails():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT email FROM contacts WHERE bounced = 1")
        emails = [row['email'] for row in cursor.fetchall()]
        logger.info(f"Fetched {len(emails)} bounced emails from DB.")
        return emails
    except Error as e:
        logger.error(f"Error fetching bounced emails from DB: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def get_replied_emails():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT email FROM contacts WHERE replied = 1")
        emails = [row['email'] for row in cursor.fetchall()]
        logger.info(f"Fetched {len(emails)} replied emails from DB.")
        return emails
    except Error as e:
        logger.error(f"Error fetching replied emails from DB: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def delete_bounced_emails(email_addresses):
    """Deletes contacts from the database based on a list of email addresses."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            logger.error("Cannot delete bounced emails: No database connection.")
            return

        cursor = connection.cursor()
        if email_addresses:
            # Create placeholders for the IN clause to prevent SQL injection
            placeholders = ','.join(['%s'] * len(email_addresses))
            query = f"DELETE FROM contacts WHERE email IN ({placeholders})"
            
            cursor.execute(query, tuple(email_addresses))
            connection.commit()
            logger.info(f"Attempted to delete {cursor.rowcount} bounced emails from contacts list.")
        else:
            logger.info("No bounced email addresses were provided to delete.")
            
    except Error as e:
        logger.error(f"Error while deleting bounced emails: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def update_contact_sent_status(contact_email, sequence_id, step_id, subject):
    """Logs a sent email event for a contact."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # First, get the contact_id from the email
        cursor.execute("SELECT id FROM contacts WHERE email = %s", (contact_email,))
        contact = cursor.fetchone()
        if not contact:
            logger.warning(f"Could not log sent status. Contact not found for email: {contact_email}")
            return

        contact_id = contact['id']

        # Now, insert into the sent_emails log
        query = """
        INSERT INTO sent_emails (contact_id, sequence_id, step_id, subject, status)
        VALUES (%s, %s, %s, %s, 'sent')
        """
        cursor.execute(query, (contact_id, sequence_id, step_id, subject))
        connection.commit()
        logger.info(f"Logged 'sent' status for contact {contact_id} in sequence {sequence_id}, step {step_id}.")

    except Error as e:
        logger.error(f"Error updating sent status for contact {contact_email}: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()