# app/utils/email_sender.py
import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Simplified imports - no more boto3 or SES models
from app.models.smtp_config import get_smtp_config_by_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email(config_id, recipient_email, subject, html_body, in_reply_to=None, references=None):
    """
    Sends an email using a specified SMTP configuration.
    """
    # Get the chosen SMTP configuration from the database
    config = get_smtp_config_by_id(config_id)
    if not config:
        logger.error(f"SMTP configuration with ID {config_id} not found.")
        return None

    host = config['host']
    port = config['port']
    username = config['username']
    password = config['password']
    use_tls = config.get('use_tls', True)
    from_email = config['from_email']
    from_name = config.get('from_name')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    if from_name:
        msg['From'] = f'"{from_name}" <{from_email}>'
    else:
        msg['From'] = from_email
    msg['To'] = recipient_email
    if in_reply_to:
        msg['In-Reply-To'] = in_reply_to
    if references:
        msg['References'] = references
    
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        server = smtplib.SMTP(host, port, timeout=10)
        if use_tls:
            server.starttls()
        
        server.login(username, password)
        server.sendmail(from_email, recipient_email, msg.as_string())
        server.quit()
        logger.info(f"Email sent via SMTP to {recipient_email} using {host}")
        # In SMTP, there's no standard message ID, so we can return a success indicator
        return "smtp-sent-successfully" 
    except Exception as e:
        logger.error(f"Failed to send email via SMTP to {recipient_email}: {e}")
        return None