# app/models/campaign.py (Debugging Version)

import mysql.connector
from mysql.connector import Error
from app.database import get_db_connection
from app.config import Config
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



def create_campaign(name, subject, body, created_by):
    """Creates a new campaign in the database."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            query = "INSERT INTO campaigns (name, subject, body, created_by) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (name, subject, body, created_by))
            conn.commit()
            return True
    except Error as e:
        logger.error(f"Error creating campaign: {e}")
        conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()

def get_campaigns():
    """Retrieves all campaigns from the database."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor(dictionary=True) as cursor:
            query = "SELECT id, name, subject, body, created_at FROM campaigns ORDER BY created_at DESC"
            cursor.execute(query)
            campaigns = cursor.fetchall()
            return campaigns
    except Error as e:
        logger.error(f"Error fetching campaigns: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            conn.close()

def get_campaign(campaign_id):
    """Retrieves a single campaign by its ID."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor(dictionary=True) as cursor:
            query = "SELECT id, name, subject, body FROM campaigns WHERE id = %s"
            cursor.execute(query, (campaign_id,))
            campaign = cursor.fetchone()
            return campaign
    except Error as e:
        logger.error(f"Error fetching campaign by ID: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            conn.close()

def delete_campaign(campaign_id):
    """Deletes a campaign from the database."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            query = "DELETE FROM campaigns WHERE id = %s"
            cursor.execute(query, (campaign_id,))
            conn.commit()
            return True
    except Error as e:
        logger.error(f"Error deleting campaign: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()