import os
from boto3 import client
from app.config import Config
import logging
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
from app.models.sequence import get_sent_emails_for_step
from app.models.contact import delete_bounced_emails, update_contact_sent_status, get_bounced_emails as get_db_bounced_emails, get_replied_emails as get_db_replied_emails
from app.models.ses_config import get_ses_configs
from app.models.log import get_db_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ses_client = None
SENDER_EMAIL = None

def initialize_ses_client():
    global ses_client, SENDER_EMAIL
    if ses_client and SENDER_EMAIL:
        return True

    configs = get_ses_configs()
    if not configs:
        logger.error("No SES configurations found in the database.")
        return False

    ses_config = configs[0]
    
    try:
        ses_client = client(
            'ses',
            region_name=ses_config['aws_region'],
            aws_access_key_id=Config.SES_ACCESS_KEY,
            aws_secret_access_key=Config.SES_SECRET_KEY
        )
        SENDER_EMAIL = ses_config['sender_email']
        logger.info(f"SES client initialized with sender: {SENDER_EMAIL} and region: {ses_config['aws_region']}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize SES client: {e}")
        return False

def get_db_connection():
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

def schedule_sequence_step(sequence_id, step):
    if not initialize_ses_client():
        logger.error("SES client not initialized. Cannot send emails.")
        return

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True) # Use dictionary cursor for easier access

        campaign_id = step['campaign_id']
        campaign_query = "SELECT subject, body FROM campaigns WHERE id = %s"
        cursor.execute(campaign_query, (campaign_id,))
        campaign = cursor.fetchone()
        if not campaign:
            logger.error(f"Campaign with ID {campaign_id} not found for sequence step {step['id']}")
            return

        subject = campaign['subject']
        body = campaign['body']

        list_id_query = "SELECT list_id FROM sequences WHERE id = %s"
        cursor.execute(list_id_query, (sequence_id,))
        list_id_result = cursor.fetchone()
        if not list_id_result:
            logger.error(f"List ID not found for sequence {sequence_id}")
            return
        list_id = list_id_result['list_id']

        contacts_query = "SELECT id, name, email, location, company_name FROM contacts WHERE list_id = %s"
        cursor.execute(contacts_query, (list_id,))
        all_contacts = cursor.fetchall()

        if not all_contacts:
            logger.info(f"No contacts found for list {list_id} of sequence {sequence_id}")
            return

        bounced_emails = get_db_bounced_emails()
        replied_emails = get_db_replied_emails()
        emails_sent_for_this_step = get_sent_emails_for_step(sequence_id, step['id'])

        valid_contacts_to_send = []
        for contact in all_contacts:
            if contact['email'] not in bounced_emails and \
               contact['email'] not in replied_emails and \
               contact['email'] not in emails_sent_for_this_step:
                valid_contacts_to_send.append(contact)

        if not valid_contacts_to_send:
            logger.info(f"No valid contacts to send to for sequence {sequence_id}, step {step['id']}")
            return

        delete_bounced_emails(bounced_emails)

        for contact in valid_contacts_to_send:
            try:
                formatted_body = body.replace('{{First Name}}', contact.get('name', '')) \
                                     .replace('{{Email}}', contact.get('email', '')) \
                                     .replace('{{Location}}', contact.get('location', '')) \
                                     .replace('{{Company}}', contact.get('company_name', ''))

                subject_line = subject
                if step.get('is_re_reply'):
                    subject_line = f"RE: {subject_line}"

                ses_client.send_email(
                    Source=SENDER_EMAIL,
                    Destination={'ToAddresses': [contact['email']]},
                    Message={
                        'Subject': {'Data': subject_line},
                        'Body': {'Html': {'Data': formatted_body}}
                    }
                )
                logger.info(f"Email sent to {contact['email']} for sequence {sequence_id}, step {step['day']} with subject: {subject_line}")
                
                # This function now handles logging the sent email to the database
                update_contact_sent_status(contact['email'], sequence_id, step['id'], subject_line)

            except Exception as e:
                logger.error(f"Failed to send email to {contact['email']} for sequence {sequence_id}, step {step['id']}: {e}")
                # Optional: You might want to log a 'failed' status here in a similar way

    except Error as e:
        logger.error(f"Database error in schedule_sequence_step for sequence {sequence_id}: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()