# scheduler.py (in your root project folder)

# --- Step 1: Load Environment Variables FIRST ---
from dotenv import load_dotenv
load_dotenv()

# --- Step 2: Import application components ---
import time
import logging
from app.models.sequence import get_due_steps, update_step_status
from app.utils.email_scheduler import process_sequence_step

# --- Standard Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main_loop():
    """
    The main scheduler loop that runs continuously.
    """
    logger.info("Scheduler process started. Press Ctrl+C to exit.")
    
    while True:
        try:
            # 1. Fetch all steps that are due to be sent.
            # This function is now updated to get the sending configuration (SES/SMTP).
            due_steps = get_due_steps()
            
            if not due_steps:
                logger.info("No due steps to process at this time.")
            else:
                logger.info(f"Found {len(due_steps)} due step(s) to process.")
                for step in due_steps:
                    try:
                        # 2. Mark the step as 'processing' to prevent it from being picked up again
                        # by the next scheduler run if this one takes a long time.
                        update_step_status(step['id'], 'processing')
                        
                        # 3. Process the individual step (which includes sending the email).
                        # This function is now updated to handle the config_type and config_id.
                        process_sequence_step(step)

                        # 4. Mark the step as 'sent' after successful processing.
                        update_step_status(step['id'], 'sent')
                        logger.info(f"Successfully processed and sent step ID: {step['id']}.")

                    except Exception as e:
                        logger.error(f"Failed to process step {step['id']}. Error: {e}", exc_info=True)
                        # Mark as 'failed' to prevent it from being retried every minute.
                        update_step_status(step['id'], 'failed')
            
            # 5. Wait for 60 seconds before checking for new steps.
            logger.info("Scheduler sleeping for 60 seconds...")
            time.sleep(60)

        except KeyboardInterrupt:
            logger.info("Scheduler process stopped by user.")
            break
        except Exception as e:
            logger.error(f"A critical error occurred in the main scheduler loop: {e}", exc_info=True)
            # In case of a major error (like DB connection loss), wait before retrying.
            time.sleep(60)

if __name__ == '__main__':
    main_loop()