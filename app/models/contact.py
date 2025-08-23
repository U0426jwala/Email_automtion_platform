# app/models/contact.py

import mysql.connector
from mysql.connector import Error
from app.database import get_db_connection
from app.config import Config
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_list(list_name, created_by):
    """Creates a new contact list."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        query = "INSERT INTO lists (list_name, created_by) VALUES (%s, %s)"
        cursor.execute(query, (list_name, created_by))
        conn.commit()
        list_id = cursor.lastrowid
        return list_id
    except Error as e:
        if e.errno == 1062:
            logger.warning(f"Attempted to create a duplicate list: {list_name}")
        else:
            logger.error(f"Error creating list: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def save_contact(list_id, name, email, location, company_name):
    """Saves a new contact to a list, checking for duplicates."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO contacts (list_id, name, email, location, company_name)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (list_id, name, email, location, company_name))
        conn.commit()
        return True
    except Error as e:
        if e.errno == 1062:
            logger.warning(f"Attempted to add duplicate email {email} to list {list_id}")
        else:
            logger.error(f"Error saving contact: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_lists():
    """Retrieves all contact lists from the database."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, list_name, records, created_at FROM lists ORDER BY created_at DESC"
        cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        logger.error(f"Error fetching lists: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_contacts_for_list(list_id):
    """Retrieves all contacts for a specific list."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, name, email, location, company_name FROM contacts WHERE list_id = %s"
        cursor.execute(query, (list_id,))
        return cursor.fetchall()
    except Error as e:
        logger.error(f"Error fetching contacts for list {list_id}: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_list_by_id(list_id):
    """Retrieves details for a single list by its ID."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, list_name, records, created_at FROM lists WHERE id = %s"
        cursor.execute(query, (list_id,))
        return cursor.fetchone()
    except Error as e:
        logger.error(f"Error fetching list by ID {list_id}: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_list_records_count(list_id):
    """Updates the 'records' count for a specific list."""
    conn = get_db_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        count_query = "SELECT COUNT(*) FROM contacts WHERE list_id = %s"
        cursor.execute(count_query, (list_id,))
        count = cursor.fetchone()[0]
        update_query = "UPDATE lists SET records = %s WHERE id = %s"
        cursor.execute(update_query, (count, list_id))
        conn.commit()
    except Error as e:
        logger.error(f"Error updating records count for list {list_id}: {e}")
    finally:
        cursor.close()
        conn.close()

def delete_contact_by_id(contact_id):
    """Deletes a single contact by their ID."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = "DELETE FROM contacts WHERE id = %s"
        cursor.execute(query, (contact_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        logger.error(f"Error deleting contact {contact_id}: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def delete_list_by_id(list_id):
    """Deletes a list and all its associated contacts."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        conn.start_transaction()
        cursor.execute("DELETE FROM contacts WHERE list_id = %s", (list_id,))
        cursor.execute("DELETE FROM lists WHERE id = %s", (list_id,))
        conn.commit()
        return True
    except Error as e:
        conn.rollback()
        logger.error(f"Error deleting list and its contacts for list_id {list_id}: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# --- MODIFICATION START: Added missing functions ---
def get_bounced_emails():
    """Fetches a set of all email addresses that have bounced."""
    conn = get_db_connection()
    if not conn:
        return set()
    try:
        cursor = conn.cursor()
        query = "SELECT email FROM bounced_emails"
        cursor.execute(query)
        # Using a set for fast 'in' lookups, e.g., 'email' in bounced_set
        bounced_set = {row[0] for row in cursor.fetchall()}
        return bounced_set
    except Error as e:
        # If the table doesn't exist yet, it's not a critical error, just log it.
        if e.errno == 1146: # Table doesn't exist
            logger.warning("The 'bounced_emails' table does not exist. Returning empty set.")
        else:
            logger.error(f"Error fetching bounced emails: {e}")
        return set()
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_replied_emails():
    """Fetches a set of all email addresses that have replied."""
    # This is a placeholder function. To make it fully work, you would need
    # a `replied_emails` table and a system to detect and log replies.
    # For now, it returns an empty set to prevent the scheduler from crashing.
    return set()
# --- MODIFICATION END ---