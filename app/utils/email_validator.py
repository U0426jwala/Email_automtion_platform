from email_validator import validate_email as validator_email, EmailNotValidError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_email(email):
    try:
        if not email or not isinstance(email, str):
            logger.error("Email is empty or not a string")
            return False
        validator_email(email)
        logger.info(f"Valid email: {email}")
        return True
    except EmailNotValidError as e:
        logger.error(f"Invalid email: {e}")
        return False