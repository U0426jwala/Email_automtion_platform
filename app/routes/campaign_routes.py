from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models.campaign import create_campaign, get_campaigns, get_campaign, delete_campaign
from app.models.contact import get_lists
from app.models.smtp_config import get_smtp_configs
from app.utils.email_sender import send_email  # Assuming direct send functionality
import logging

logger = logging.getLogger(__name__)

campaign_bp = Blueprint('campaign', __name__, url_prefix='/campaigns')

@campaign_bp.route('/list')
@login_required
def campaigns_list():
    """Renders the main campaigns page with a list of campaigns."""
    campaigns = get_campaigns()
    lists = get_lists()
    smtp_configs = get_smtp_configs(current_user.id)
    return render_template('campaign_list.html',
                           campaigns=campaigns,
                           lists=lists,
                           smtp_configs=smtp_configs)

@campaign_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_campaign_route():
    """Handles the creation of a new campaign."""
    # Retrieve the Gemini API key from the application config
    gemini_api_key = current_app.config.get('GEMINI_API_KEY')

    if request.method == 'POST':
        name = request.form.get('name')
        subject = request.form.get('subject')
        body = request.form.get('body')

        if not all([name, subject, body]):
            flash('All fields are required.', 'error')
            # Pass the key back to the template even if there's an error
            return render_template('create_campaign.html', gemini_api_key=gemini_api_key)

        if create_campaign(name, subject, body, current_user.id):
            flash('Campaign created successfully!', 'success')
            return redirect(url_for('campaign.campaigns_list'))
        else:
            flash('Failed to create campaign.', 'error')

    # Pass the key to the template for the initial GET request
    return render_template('create_campaign.html', gemini_api_key=gemini_api_key)

@campaign_bp.route('/preview/<int:campaign_id>')
@login_required
def preview_campaign_route(campaign_id):
    """Shows a preview of a single campaign."""
    campaign = get_campaign(campaign_id)
    if not campaign:
        flash('Campaign not found.', 'error')
        return redirect(url_for('campaign.campaigns_list'))
    return render_template('preview_campaign.html', campaign=campaign)

@campaign_bp.route('/delete/<int:campaign_id>', methods=['POST'])
@login_required
def delete_campaign_route(campaign_id):
    """Deletes a campaign."""
    if delete_campaign(campaign_id):
        flash('Campaign deleted successfully.', 'success')
    else:
        flash('Error deleting campaign.', 'error')
    return redirect(url_for('campaign.campaigns_list'))

@campaign_bp.route('/send', methods=['POST'])
@login_required
def send_campaign_route():
    """Handles sending a direct (non-sequence) campaign."""
    campaign_id = request.form.get('campaign_id')
    list_id = request.form.get('list_id')
    config_id = request.form.get('config_id')

    # Basic validation
    if not all([campaign_id, list_id, config_id]):
        flash('Campaign, List, and Sender must be selected.', 'error')
        return redirect(url_for('campaign.campaigns_list'))

    # In a real app, you would queue this as a background job
    # For simplicity, we'll process it directly here.
    flash(f'Campaign sending initiated to list {list_id}. This could take a moment.', 'info')
    # Add your logic here to fetch all contacts from the list and loop through them,
    # calling send_email for each one.
    
    return redirect(url_for('campaign.campaigns_list'))
