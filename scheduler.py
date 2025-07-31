import time
import logging
from datetime import datetime, timedelta
from app.models.sequence import (
    get_sequences,
    get_sequence_steps,
    update_sequence_status,
    create_sequence_step,
    get_latest_sent_log_time  # Required helper function from sequence model
)
from app.utils.email_scheduler import schedule_sequence_step # The utility that sends the emails

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration for the automated flow ---
SEQUENCE_FLOW = {
    "max_days": 2,  # The total number of steps in the sequence
    "follow_up_delay_hours": 24  # How long to wait before creating the Day 2 step
}

def process_active_sequences():
    """
    Main function to process all active email sequences.
    This function will be called repeatedly by the scheduler's main loop.
    """
    logger.info("Scheduler starting new cycle: Processing active sequences...")
    # Fetch only sequences that are currently 'active'
    active_sequences = get_sequences_by_status('active')

    if not active_sequences:
        logger.info("No active sequences found in this cycle.")
        return

    for seq in active_sequences:
        sequence_id = seq['id']
        logger.info(f"Processing sequence ID: {sequence_id} ('{seq['name']}')")

        try:
            # --- Part 1: Send any existing steps that are due to be sent ---
            # Your email_scheduler utility is responsible for checking if a contact
            # has already received the email for this step.
            steps = get_sequence_steps(sequence_id)
            if steps:
                # The logic to check *when* a step is due should be here if needed.
                # For this design, we assume if a step exists, we attempt to process it.
                # The 'schedule_sequence_step' function contains the core sending logic.
                for step in steps:
                    logger.info(f"Dispatching task to send emails for sequence {sequence_id}, Day {step['day']}")
                    schedule_sequence_step(sequence_id, step)
            
            # --- Part 2: Check if we need to create the next follow-up step ---
            create_next_follow_up_step(seq)

        except Exception as e:
            logger.error(f"An unexpected error occurred while processing sequence {sequence_id}: {e}", exc_info=True)


def create_next_follow_up_step(sequence_data):
    """
    Checks if a follow-up step (e.g., Day 2) needs to be created automatically.
    This is the core of the backend automation.
    """
    sequence_id = sequence_data['id']
    steps = get_sequence_steps(sequence_id)
    current_max_day = max([step['day'] for step in steps]) if steps else 0

    # If the sequence has already reached its final step, mark it as 'finished'.
    if current_max_day >= SEQUENCE_FLOW['max_days']:
        logger.info(f"Sequence {sequence_id} is already complete. Marking as 'finished'.")
        update_sequence_status(sequence_id, 'finished')
        return

    # To schedule Day 2, we must know when Day 1 was sent.
    # We get the timestamp of the last successfully sent email for this sequence.
    last_sent_time = get_latest_sent_log_time(sequence_id)
    
    # If no emails have been sent yet (e.g., Day 1 is still processing or hasn't started),
    # we can't schedule the next step.
    if not last_sent_time:
        logger.info(f"No sent logs for sequence {sequence_id}. Cannot create follow-up yet.")
        return

    # Check if enough time has passed to schedule the next step
    time_to_schedule = last_sent_time + timedelta(hours=SEQUENCE_FLOW['follow_up_delay_hours'])
    
    if datetime.now() >= time_to_schedule:
        next_day = current_max_day + 1
        logger.info(f"It's time to create the Day {next_day} step for sequence {sequence_id}.")

        # For the follow-up, we reuse the campaign from Day 1.
        day_one_step = next((step for step in steps if step['day'] == 1), None)
        if not day_one_step:
            logger.error(f"Cannot create Day {next_day} step because Day 1 step is missing for sequence {sequence_id}.")
            return

        campaign_id_for_follow_up = day_one_step['campaign_id']

        # Create the new follow-up step in the database
        create_sequence_step(
            sequence_id=sequence_id,
            day=next_day,
            campaign_id=campaign_id_for_follow_up,
            schedule_offset_minutes=0,  # Offset is handled by our time delay logic
            is_re_reply=True  # IMPORTANT: This triggers the "RE:" subject
        )
        logger.info(f"Successfully created Day {next_day} follow-up step for sequence {sequence_id}.")
    else:
        logger.info(f"Not yet time to create follow-up for sequence {sequence_id}. Next check after {time_to_schedule}.")


def get_sequences_by_status(status):
    """Helper function to filter sequences by their status."""
    all_sequences = get_sequences()
    return [s for s in all_sequences if s['status'] == status]


def run_scheduler():
    """The main loop to run the scheduler service continuously."""
    logger.info("Starting email sequence scheduler service.")
    while True:
        try:
            process_active_sequences()
        except Exception as e:
            logger.error(f"A critical error occurred in the main scheduler loop: {e}", exc_info=True)
        
        # Wait for 60 seconds before the next cycle
        logger.info("Scheduler cycle complete. Waiting for 60 seconds...")
        time.sleep(60)

if __name__ == "__main__":
    run_scheduler()