# scheduler.py

import mysql.connector
from mysql.connector import Error
from app.config import Config
import logging
import os
import time
from app.utils.email_scheduler import schedule_sequence_step
# Corrected imports: only keep what's needed
from app.models.sequence import update_step_status

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
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

def process_due_steps():
    """
    Finds due steps (schedule_time <= NOW and status='scheduled'), 
    sets to 'active', sends emails, then sets to 'finished'.
    """
    connection = get_db_connection()
    if not connection: 
        logger.error("Scheduler: Could not connect to DB. Skipping run.")
        return 0
    
    processed_count = 0
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
                SELECT ss.id, ss.sequence_id
                FROM sequence_steps ss
                WHERE ss.status = 'scheduled' AND ss.schedule_time <= NOW()
            """
            cursor.execute(query)
            due_steps = cursor.fetchall()

            if not due_steps:
                logger.info("Scheduler: No due steps to process at this time.")
                return 0
            
            logger.info(f"Scheduler: Found {len(due_steps)} due steps to process.")
            for step in due_steps:
                try:
                    update_step_status(step['id'], 'active')
                    schedule_sequence_step(step['sequence_id'], step)
                    update_step_status(step['id'], 'finished')
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Scheduler: Failed to process step {step['id']}. Error: {e}", exc_info=True)
                    # Mark as failed to prevent retrying constantly
                    update_step_status(step['id'], 'failed')

    except Error as e:
        logger.error(f"Scheduler: Database error during step processing: {e}", exc_info=True)
    finally:
        if connection.is_connected():
            connection.close()
            
    logger.info(f"Scheduler: Run finished. Processed {processed_count} steps.")
    return processed_count

if __name__ == '__main__':
    logger.info("Starting scheduler process in continuous mode. Press Ctrl+C to exit.")
    while True:
        logger.info("Scheduler waking up...")
        process_due_steps()
        logger.info("Scheduler sleeping for 60 seconds...")
        time.sleep(60)