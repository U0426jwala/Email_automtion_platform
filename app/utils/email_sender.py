# app/utils/email_sender.py
import boto3
from botocore.exceptions import ClientError
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email(recipient_email, subject, html_body, in_reply_to=None, references=None):
    """
    Sends an email using AWS SES with optional headers for threading.
    Returns the Message ID on success, None on failure.
    """
    aws_region = os.getenv('AWS_REGION')
    sender_email = os.getenv('SENDER_EMAIL')

    if not sender_email or not aws_region:
        logger.error("FATAL: SENDER_EMAIL or AWS_REGION environment variable is not set.")
        return None

    ses_client = boto3.client('ses', region_name=aws_region)
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    # CRITICAL: These headers create the email thread in clients like Gmail/Outlook
    if in_reply_to:
        msg['In-Reply-To'] = in_reply_to
    if references:
        msg['References'] = references

    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        response = ses_client.send_raw_email(
            Source=msg['From'],
            Destinations=[msg['To']],
            RawMessage={'Data': msg.as_string()}
        )
        message_id = response['MessageId']
        logger.info(f"Email sent to {recipient_email}. Message ID: {message_id}")
        return message_id
    except ClientError as e:
        logger.error(f"Failed to send email to {recipient_email}: {e.response['Error']['Message']}")
        return None