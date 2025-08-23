from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
import os
import time
import json
import logging
import boto3
import mysql.connector
from mysql.connector import Error

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Database Connection (copied from your existing code) ---
def get_db_connection():
    """Establishes and returns a database connection."""
    try:
        db_password = os.getenv('MYSQL_PASSWORD')
        return mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=db_password,
            database=os.getenv('MYSQL_DB'),
            connection_timeout=10
        )
    except Error as e:
        logger.error(f"Error establishing database connection: {e}")
        return None

# --- Function to add a bounced email to your database ---
def add_email_to_bounce_list(email):
    """Inserts a bounced email into the bounced_emails table."""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            # Use INSERT IGNORE to prevent errors if the email already exists
            query = "INSERT IGNORE INTO bounced_emails (email) VALUES (%s)"
            cursor.execute(query, (email,))
            connection.commit()
            if cursor.rowcount > 0:
                logger.info(f"Added '{email}' to the bounce list.")
            return True
    except Error as e:
        logger.error(f"Database error adding bounced email {email}: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            connection.close()

# --- Main Application Loop ---
def main_loop():
    logger.info("Bounce handler process started.")
    
    # Configure Boto3 SQS client
    sqs_client = boto3.client(
        'sqs',
        region_name=os.getenv('AWS_REGION'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    # Get the SQS Queue URL
    try:
        queue_name = 'ses-bounces-queue'
        response = sqs_client.get_queue_url(QueueName=queue_name)
        queue_url = response['QueueUrl']
        logger.info(f"Successfully connected to SQS queue: {queue_name}")
    except sqs_client.exceptions.QueueDoesNotExist:
        logger.error(f"The SQS queue '{queue_name}' does not exist. Please create it in the AWS console.")
        return
    except Exception as e:
        logger.error(f"Error getting SQS queue URL: {e}")
        return

    while True:
        try:
            # Poll the queue for messages
            response = sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10, # Process up to 10 messages at a time
                WaitTimeSeconds=20      # Wait up to 20 seconds for messages
            )

            messages = response.get('Messages', [])
            if not messages:
                logger.info("No new bounce messages in the queue. Waiting...")
                continue

            for message in messages:
                try:
                    # The body of the SQS message contains JSON from SNS
                    body = json.loads(message['Body'])
                    # The 'Message' key within that JSON is also a JSON string
                    ses_notification = json.loads(body['Message'])
                    
                    if ses_notification.get('notificationType') == 'Bounce':
                        bounce_info = ses_notification.get('bounce', {})
                        bounced_recipients = bounce_info.get('bouncedRecipients', [])
                        
                        for recipient in bounced_recipients:
                            email_address = recipient.get('emailAddress')
                            if email_address:
                                add_email_to_bounce_list(email_address)

                    # Delete the message from the queue after processing
                    sqs_client.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                except Exception as e:
                    logger.error(f"Error processing a single SQS message: {e}")

        except KeyboardInterrupt:
            logger.info("Bounce handler process stopped by user.")
            break
        except Exception as e:
            logger.error(f"An error occurred in the main bounce handler loop: {e}")
            time.sleep(30) # Wait before retrying after a major error

if __name__ == '__main__':
    main_loop()