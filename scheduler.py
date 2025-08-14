# scheduler.py
from dotenv import load_dotenv
load_dotenv()
import time
import logging
from app.models.sequence import get_due_steps, update_step_status
from app.utils.email_scheduler import process_sequence_step

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main_loop():
    logger.info("Scheduler process started. Press Ctrl+C to exit.")
    while True:
        try:
            due_steps = get_due_steps()
            if not due_steps:
                logger.info("No due steps to process at this time.")
            else:
                logger.info(f"Found {len(due_steps)} due step(s) to process.")
                for step in due_steps:
                    # Mark step as 'processing' to prevent re-sending in case of long task
                    update_step_status(step['id'], 'processing')
                    
                    process_sequence_step(step)

                    # Mark step as 'sent' after processing
                    update_step_status(step['id'], 'sent')
            
            # Wait for the next cycle
            logger.info("Scheduler sleeping for 60 seconds...")
            time.sleep(60)

        except KeyboardInterrupt:
            logger.info("Scheduler process stopped by user.")
            break
        except Exception as e:
            logger.error(f"An error occurred in the main scheduler loop: {e}", exc_info=True)
            # Wait before retrying to prevent rapid-fire errors
            time.sleep(60)

if __name__ == '__main__':
    main_loop()