# app/routes/campaign_routes.py

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models.campaign import create_campaign, get_campaigns, get_campaign
# CORRECTED: The import name is now 'get_contacts_for_list'
from app.models.contact import get_lists, get_contacts_for_list
from app.utils.email_sender import send_email
from app.models.log import SentEmail
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

campaign_bp = Blueprint('campaign', __name__)

@campaign_bp.route('/list', methods=['GET'])
@login_required
def campaign_list():
    campaigns = get_campaigns()
    lists = get_lists()
    return render_template('campaign_list.html', campaigns=campaigns, lists=lists)

@campaign_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_campaign_view():
    gemini_api_key = os.getenv('GEMINI_API_KEY', '')
    if request.method == 'POST':
        name = request.form.get('name')
        subject = request.form.get('subject')
        body = request.form.get('body')
        created_by = current_user.username
        if not all([name, subject, body]):
            flash('All fields are required', 'error')
            return render_template('create_campaign.html', gemini_api_key=gemini_api_key)
        create_campaign(name, subject, body, created_by)
        flash('Campaign created successfully!', 'success')
        return redirect(url_for('campaign.campaign_list'))
    return render_template('create_campaign.html', gemini_api_key=gemini_api_key)

@campaign_bp.route('/send/<int:campaign_id>', methods=['POST'])
@login_required
def send_campaign(campaign_id):
    list_id = request.form.get('list_id')
    if not list_id:
        flash("You must select a contact list.", "error")
        return redirect(url_for('campaign.campaign_list'))

    campaign = get_campaign(campaign_id)
    # CORRECTED: Using the correct function name here
    contacts = get_contacts_for_list(list_id)

    if not campaign or not contacts:
        flash("Campaign or contacts not found.", "error")
        return redirect(url_for('campaign.campaign_list'))

    sent_count, failed_count = 0, 0
    for contact in contacts:
        body = campaign['body'].replace('{{First Name}}', contact.get('name', '')).replace('{{Company}}', contact.get('company_name', ''))
        subject = campaign['subject'].replace('{{First Name}}', contact.get('name', ''))
        
        message_id = send_email(contact['email'], subject, body)
        
        if message_id:
            # CORRECTED: Logging call now passes the correct arguments
            SentEmail.log_email(
                user_id=current_user.id,
                contact_id=contact['id'], # Passing contact ID instead of email
                subject=subject,
                status='sent',
                campaign_id=campaign_id,
                message_id=message_id
            )
            sent_count += 1
        else:
            SentEmail.log_email(
                user_id=current_user.id,
                contact_id=contact['id'],
                subject=subject,
                status='failed',
                campaign_id=campaign_id
            )
            failed_count += 1

    flash(f"Campaign sending process completed. Sent: {sent_count}, Failed: {failed_count}", "success")
    return redirect(url_for('campaign.campaign_list'))

@campaign_bp.route('/preview/<int:campaign_id>', methods=['GET'])
@login_required
def preview_campaign(campaign_id):
    campaign = get_campaign(campaign_id)
    body = campaign.get('body', '').replace('{{First Name}}', 'John').replace('{{Company}}', 'Example Corp')
    return render_template('preview_campaign.html', campaign=campaign, body=body)