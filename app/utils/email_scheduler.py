# app/utils/email_scheduler.py

import logging
from datetime import timedelta
from app.celery_app import celery
from app.models.sequence import get_due_steps, update_step_status, get_last_sent_email_for_contact
from app.models.contact import get_contacts_for_list, get_bounced_emails, get_replied_emails
from app.models.smtp_config import get_smtp_config_by_id
from app.models.log import SentEmail
from .email_sender import send_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60.0, process_due_steps.s(), name='check for due emails every 60s')

@celery.task
def process_due_steps():
    logger.info("Scheduler task started: Fetching due email steps...")
    due_steps = get_due_steps()
    if not due_steps:
        logger.info("No due steps found.")
        return

    bounced_emails = get_bounced_emails()
    replied_emails = get_replied_emails()

    for step in due_steps:
        logger.info(f"Processing step ID {step['id']} for sequence {step['sequence_id']}")
        
        update_step_status(step['id'], 'processing')

        smtp_config = get_smtp_config_by_id(step['config_id'])
        if not smtp_config:
            logger.error(f"SMTP config not found for step {step['id']}. Skipping.")
            update_step_status(step['id'], 'failed')
            continue

        contacts = get_contacts_for_list(step['list_id'])
        for contact in contacts:
            if contact['email'] in bounced_emails or contact['email'] in replied_emails:
                logger.info(f"Skipping {contact['email']} for sequence {step['sequence_id']} (bounced/replied).")
                continue

            try:
                # --- MODIFICATION START: Threading Logic ---
                in_reply_to = None
                references = None
                
                # Default to the current campaign's subject
                personalized_subject = step['campaign_subject'].format(
                    name=contact['name'],
                    company_name=contact['company_name'],
                    location=contact['location']
                )

                # Default to the current campaign's body
                personalized_body = step['campaign_body'].format(
                    name=contact['name'],
                    company_name=contact['company_name'],
                    location=contact['location']
                )
                
                # Rebuild the entire email body, including the reply chain
                if step['is_re_reply']:
                    last_email = get_last_sent_email_for_contact(step['sequence_id'], contact['id'])
                    
                    if last_email:
                        in_reply_to = last_email['message_id']
                        last_references = last_email.get('references') or last_email['message_id']
                        references = f"{last_references} {in_reply_to}"

                        # Add "Re:" to the subject if it's not already there
                        if not personalized_subject.lower().startswith('re:'):
                            personalized_subject = f"Re: {personalized_subject}"

                        # Build the quoted HTML block
                        original_sent_at = last_email['sent_at'].strftime('%d %b %Y %H:%M') if last_email.get('sent_at') else 'N/A'
                        from_name = smtp_config.get('from_name', smtp_config['from_email'])
                        to_name = contact.get('name', contact.get('email', ''))

                        quoted_html = f"""
                            <br>
                            <div style="font-size: 10pt; font-family: Tahoma, 'sans-serif';">
                                <hr style="display:inline-block;width:98%;border-style:solid;border-width:1px;border-color:#E1E1E1;">
                                <b>From:</b> {from_name}<br>
                                <b>Sent:</b> {original_sent_at}<br>
                                <b>To:</b> {to_name} &lt;{contact['email']}&gt;<br>
                                <b>Subject:</b> {last_email['subject']}<br>
                            </div>
                            <br>
                            <div style="background-color:#EFEFEF; padding: 10px; border: 1px solid #CCCCCC;">
                                {last_email['campaign_body']}
                            </div>
                        """
                        # Combine the new content with the quoted content
                        personalized_body += quoted_html
                
                # Pass the headers and the new, combined HTML body to the sender
                message_id, final_references = send_email(smtp_config, contact['email'], personalized_subject, personalized_body, in_reply_to, references)
                
                if message_id:
                    SentEmail.log_email(
                        user_id=step['user_id'], 
                        contact_id=contact['id'], 
                        subject=personalized_subject, 
                        status='sent', 
                        campaign_id=step['campaign_id'], 
                        message_id=message_id, 
                        references=final_references,
                        sequence_id=step['sequence_id'],
                        step_id=step['id']
                    )
                    logger.info(f"Email sent to {contact['email']} for step {step['id']}")
                else:
                    raise Exception("send_email function failed to return a message_id")

            except Exception as e:
                logger.error(f"Failed to send email to {contact['email']} for step {step['id']}: {e}")
                SentEmail.log_email(
                    user_id=step['user_id'], 
                    contact_id=contact['id'], 
                    subject=personalized_subject, 
                    status='failed', 
                    campaign_id=step['campaign_id'],
                    sequence_id=step['sequence_id'],
                    step_id=step['id']
                )
                # --- MODIFICATION END ---
        
        # --- FIX: Ensure this is correctly outside the inner 'for' loop but inside the outer 'for' loop.
        update_step_status(step['id'], 'sent')
        logger.info(f"Finished processing step {step['id']}.")