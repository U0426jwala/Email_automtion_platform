import logging
import time
from datetime import datetime
import re # Using the regex module
from app.celery_app import celery
from app.models.sequence import get_due_steps_for_utc_time, update_step_status, get_last_sent_email_for_contact
from app.models.contact import get_contacts_for_list, get_bounced_emails, get_replied_emails
from app.models.smtp_config import get_smtp_config_by_id
from app.models.log import SentEmail
from .email_sender import send_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FINAL, MOST ROBUST HELPER FUNCTION ---
def _personalize_content(content, contact):
    """
    Replaces {{placeholders}} case-insensitively, handles spaces within
    placeholders, and converts newlines to <br> tags.
    """
    if not content:
        return ""

    # 1. Get and split the full name from the contact dictionary.
    full_name = contact.get('name', '').strip()
    first_name = ""
    last_name = ""
    if full_name:
        parts = full_name.split(' ', 1)
        first_name = parts[0]
        if len(parts) > 1:
            last_name = parts[1]

    # 2. Create a dictionary of the available data with simple, lowercase keys.
    replacements = {
        'firstname': first_name,
        'lastname': last_name,
        'company': contact.get('company_name', ''),
        'email': contact.get('email', '')
    }

    # 3. Use a regular expression to find all {{placeholders}} case-insensitively.
    def replace_func(match):
        # Get the captured placeholder (e.g., "First Name")
        captured_key = match.group(1)
        # Process it: make it lowercase and remove all spaces (e.g., "first name" -> "firstname")
        processed_key = captured_key.lower().replace(' ', '')
        # Look up the clean key in our dictionary
        return replacements.get(processed_key, match.group(0))

    # This UPDATED regex `[\w\s]+` now matches word characters AND spaces.
    content = re.sub(r'\{\{([\w\s]+)\}\}', replace_func, content, flags=re.IGNORECASE)
    
    # 4. Convert plain text newlines to HTML line breaks.
    content = content.replace('\n', '<br>')

    return content.strip()
# --- End of function ---


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60.0, process_due_steps.s(), name='check for due emails every 60s')

@celery.task
def process_due_steps():
    now_utc = datetime.utcnow()
    due_steps = get_due_steps_for_utc_time(now_utc)
    if not due_steps:
        return

    bounced_emails = get_bounced_emails()
    replied_emails = get_replied_emails()

    for step in due_steps:
        update_step_status(step['id'], 'processing')
        smtp_config = get_smtp_config_by_id(step['config_id'])
        if not smtp_config:
            update_step_status(step['id'], 'failed')
            continue

        contacts = get_contacts_for_list(step['list_id'])
        for contact in contacts:
            if contact['email'] in bounced_emails or contact['email'] in replied_emails:
                continue
            
            personalized_subject, personalized_body, in_reply_to, references = None, None, None, None
            
            try:
                campaign_id_for_log = step.get('campaign_id')
                from_name = smtp_config.get('from_name', '')
                from_email = smtp_config.get('from_email', '')
                to_email = contact['email']

                if step['step_number'] == 1:
                    personalized_subject = _personalize_content(step['campaign_subject'], contact)
                    personalized_body = _personalize_content(step['campaign_body'], contact)
                else:
                    last_email = get_last_sent_email_for_contact(step['sequence_id'], contact['id'])
                    
                    if last_email and last_email.get('message_id'):
                        original_subject = last_email.get('subject', '')
                        
                        personalized_subject = (
                            f"Re: {original_subject}" if not original_subject.lower().startswith('re:') else original_subject
                        )

                        original_from = f"{last_email.get('from_name')} <{last_email.get('from_email')}>"
                        original_sent = last_email.get('sent_at').strftime('%d %B %Y %H:%M')
                        original_to = last_email.get('to_email')
                        
                        quote_header = (
                            f'<div style="border-top: 1px solid #E1E1E1; margin-top: 20px; padding-top: 10px;">'
                            f'<b>From:</b> {original_from}<br>'
                            f'<b>Sent:</b> {original_sent}<br>'
                            f'<b>To:</b> {original_to}<br>'
                            f'<b>Subject:</b> {original_subject}'
                            f'</div>'
                        )
                        
                        reply_content = _personalize_content(step['reply_body'], contact)
                        
                        personalized_body = f"""
                        <p>{reply_content}</p>
                        <br>
                        {quote_header}
                        <blockquote style="border-left: 2px solid #ccc; padding-left: 10px; margin-left: 5px; color: #666;">
                        {last_email.get('body', '')}
                        </blockquote>
                        """

                        in_reply_to = last_email.get('message_id')
                        parent_references = last_email.get('references')
                        references = f"{parent_references} {in_reply_to}" if parent_references else in_reply_to
                    else:
                        logger.warning(f"Could not find previous email for {contact['email']}. Sending as new thread.")
                        personalized_subject = _personalize_content("Re: Following up", contact)
                        personalized_body = _personalize_content(step['reply_body'], contact)
                
                if not personalized_subject or not personalized_body:
                    continue

                message_id, final_references, final_body = send_email(
                    smtp_config, to_email, personalized_subject, personalized_body, in_reply_to, references
                )

                if message_id:
                    SentEmail.log_email(
                        user_id=step['user_id'], contact_id=contact['id'], subject=personalized_subject, 
                        status='sent', campaign_id=campaign_id_for_log, message_id=message_id, 
                        references=final_references, sequence_id=step['sequence_id'], step_id=step['id'],
                        body=final_body, from_name=from_name, from_email=from_email, to_email=to_email
                    )
            except Exception as e:
                logger.error(f"Failed to process email for {contact['email']} in step {step['id']}: {e}")
            finally:
                logger.info("Waiting for 5 seconds...")
                time.sleep(5)
        
        update_step_status(step['id'], 'sent')