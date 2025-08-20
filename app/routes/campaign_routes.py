# app/routes/campaign_routes.py

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.campaign import create_campaign, get_campaigns, get_campaign, delete_campaign 
from app.models.contact import get_lists, get_contacts_for_list
# --- MODIFICATION START ---
# Simplified imports: Removed SES, kept SMTP and the new sender
from app.utils.email_sender import send_email
from app.models.smtp_config import get_smtp_configs
# --- MODIFICATION END ---
from app.models.log import SentEmail
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

campaign_bp = Blueprint('campaign', __name__)

@campaign_bp.route('/list', methods=['GET'])
@login_required
def campaign_list():
    """ Fetches campaigns, lists, and SMTP configurations for the mailer page. """
    campaigns = get_campaigns()
    lists = get_lists()
    # --- MODIFICATION START ---
    # Only fetch SMTP configs
    smtp_configs = get_smtp_configs(current_user.id)
    # --- MODIFICATION END ---
    
    return render_template('campaign_list.html', 
                           campaigns=campaigns, 
                           lists=lists, 
                           smtp_configs=smtp_configs)

@campaign_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_campaign_view():
    gemini_api_key = os.getenv('GEMINI_API_KEY', '')
    if request.method == 'POST':
        name = request.form.get('name')
        subject = request.form.get('subject')
        body = request.form.get('body')
        
        if not all([name, subject, body]):
            flash('All fields are required', 'error')
            return render_template('create_campaign.html', gemini_api_key=gemini_api_key)
            
        create_campaign(name, subject, body, current_user.id)
        flash('Campaign created successfully!', 'success')
        return redirect(url_for('campaign.campaign_list'))
        
    return render_template('create_campaign.html', gemini_api_key=gemini_api_key)

@campaign_bp.route('/send/<int:campaign_id>', methods=['POST'])
@login_required
def send_campaign(campaign_id):
    """ Handles sending a campaign using the selected SMTP configuration. """
    list_id = request.form.get('list_id')
    # --- MODIFICATION START ---
    # Logic is simplified to only get the SMTP config ID
    config_id = request.form.get('sending_config')

    if not list_id or not config_id:
        flash("You must select a contact list and an SMTP configuration.", "error")
        return redirect(url_for('campaign.campaign_list'))

    config_id = int(config_id)
    # --- MODIFICATION END ---

    campaign = get_campaign(campaign_id)
    contacts = get_contacts_for_list(list_id)

    if not campaign or not contacts:
        flash("Campaign or contacts not found.", "error")
        return redirect(url_for('campaign.campaign_list'))

    sent_count, failed_count = 0, 0
    for contact in contacts:
        body = campaign['body'].replace('{{First Name}}', contact.get('name', '')).replace('{{Company}}', contact.get('company_name', ''))
        subject = campaign['subject'].replace('{{First Name}}', contact.get('name', ''))
        
        # --- MODIFICATION START ---
        # Call the simplified send_email function
        message_id = send_email(
            config_id=config_id,
            recipient_email=contact['email'],
            subject=subject,
            html_body=body
        )
        # --- MODIFICATION END ---
        
        if message_id:
            SentEmail.log_email(user_id=current_user.id, contact_id=contact['id'], subject=subject, status='sent', campaign_id=campaign_id, message_id=message_id)
            sent_count += 1
        else:
            SentEmail.log_email(user_id=current_user.id, contact_id=contact['id'], subject=subject, status='failed', campaign_id=campaign_id)
            failed_count += 1

    flash(f"Campaign sending process completed. Sent: {sent_count}, Failed: {failed_count}", "success")
    return redirect(url_for('campaign.campaign_list'))

@campaign_bp.route('/preview/<int:campaign_id>', methods=['GET'])
@login_required
def preview_campaign(campaign_id):
    campaign = get_campaign(campaign_id)
    if not campaign:
        flash("Campaign not found.", "error")
        return redirect(url_for('campaign.campaign_list'))
    return render_template('preview_campaign.html', campaign=campaign)

@campaign_bp.route('/delete/<int:campaign_id>', methods=['POST'])
@login_required
def delete_campaign_route(campaign_id):
    if delete_campaign(campaign_id):
        flash('Campaign deleted successfully.', 'success')
    else:
        flash('Error deleting campaign.', 'error')
    return redirect(url_for('campaign.campaign_list'))