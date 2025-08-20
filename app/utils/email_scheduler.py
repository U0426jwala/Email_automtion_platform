# app/utils/email_scheduler.py

import logging
from app.models.sequence import get_db_connection, get_last_sent_email_for_contact
from app.models.contact import get_contacts_for_list, get_bounced_emails, get_replied_emails
from app.models.log import SentEmail
from app.utils.email_sender import send_email
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def build_reply_body(new_body_template, prev_email, contact_name):
    new_body = new_body_template.replace('{{First Name}}', contact_name)
    prev_body = prev_email.get('campaign_body', '')
    prev_sent_at = prev_email.get('sent_at')
    prev_body_personalized = prev_body.replace('{{First Name}}', contact_name)
    sent_date_str = "an earlier date"
    if prev_sent_at:
        sent_date_str = prev_sent_at.strftime("%a, %b %d, %Y at %I:%M %p")
    sender_email = os.getenv('SENDER_EMAIL', 'you')

    return f"""
    <div style="font-family: sans-serif; font-size: 1rem;">{new_body}</div>
    <br>
    <div style="color: #5e5e5e;">
        On {sent_date_str}, {sender_email} wrote:
        <blockquote style="margin: 0 0 0 .8ex; border-left: 1px #ccc solid; padding-left: 1ex;">
            {prev_body_personalized}
        </blockquote>
    </div>
    """

# --- MODIFICATION: Changed the function name back to what scheduler.py expects ---
def process_sequence_step(step):
    """Processes a single due step, now using the specified sending configuration."""
    logger.info(f"Processing Step ID: {step['id']} for Sequence ID: {step['sequence_id']}")
    
    try:
        all_contacts = get_contacts_for_list(step['list_id'])
        if not all_contacts:
            logger.warning(f"No contacts found for list ID {step['list_id']}. Skipping step.")
            return

        bounced_emails = get_bounced_emails()
        replied_emails = get_replied_emails()

        valid_contacts = [
            c for c in all_contacts 
            if c['email'] not in bounced_emails and c['email'] not in replied_emails
        ]

        logger.info(f"Found {len(valid_contacts)} valid contacts to email for Step ID: {step['id']}.")

        for contact in valid_contacts:
            subject = step['campaign_subject']
            body = step['campaign_body']
            in_reply_to = None
            references = None

            if step.get('is_re_reply'):
                previous_email = get_last_sent_email_for_contact(step['sequence_id'], contact['id'])
                if previous_email:
                    in_reply_to = previous_email.get('message_id')
                    references = previous_email.get('message_id')
                    if not previous_email.get('subject', '').lower().startswith('re:'):
                         subject = f"Re: {previous_email.get('subject', '')}"
                    else:
                         subject = previous_email.get('subject', '')
                    body = build_reply_body(body, previous_email, contact['name'])

            message_id = send_email(
                config_type=step['config_type'],
                config_id=step['config_id'],
                recipient_email=contact['email'],
                subject=subject.replace('{{First Name}}', contact.get('name', '')),
                html_body=body.replace('{{First Name}}', contact.get('name', '')),
                in_reply_to=in_reply_to,
                references=references
            )

            user_id_for_log = step.get('user_id')

            if message_id:
                SentEmail.log_email(
                    user_id=user_id_for_log,
                    contact_id=contact['id'],
                    subject=subject,
                    status='sent',
                    campaign_id=step.get('campaign_id'),
                    sequence_id=step.get('sequence_id'),
                    step_id=step.get('id'),
                    message_id=message_id
                )
            else:
                SentEmail.log_email(
                    user_id=user_id_for_log,
                    contact_id=contact['id'],
                    subject=subject,
                    status='failed',
                    campaign_id=step.get('campaign_id'),
                    sequence_id=step.get('sequence_id'),
                    step_id=step.get('id')
                )

    except Exception as e:
        logger.error(f"An unexpected error occurred in process_sequence_step for step ID {step['id']}: {e}", exc_info=True)