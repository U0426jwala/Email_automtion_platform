from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.campaign import create_campaign, get_campaigns, get_campaign
import logging
import os # Import os to get environment variables

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

campaign_bp = Blueprint('campaign', __name__)

@campaign_bp.route('/list', methods=['GET'])
@login_required
def campaign_list():
    campaigns = get_campaigns()
    return render_template('campaign_list.html', campaigns=campaigns)

@campaign_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_campaign_view():
    # Get Gemini API key from environment variables
    gemini_api_key = os.getenv('GEMINI_API_KEY', '')

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            subject = request.form.get('subject')
            body = request.form.get('body')
            created_by = current_user.username

            if not all([name, subject, body]):
                flash('All fields (name, subject, body) are required', 'error')
                # Re-render the form with the API key
                return render_template('create_campaign.html', gemini_api_key=gemini_api_key)

            campaign_id = create_campaign(name, subject, body, created_by)
            if campaign_id:
                flash('Campaign created successfully!', 'success')
                return redirect(url_for('campaign.campaign_list'))
            else:
                flash('Failed to create campaign.', 'error')

        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            flash(f'An unexpected error occurred: {str(e)}', 'error')
        
        # In case of any error, re-render the form with the API key
        return render_template('create_campaign.html', gemini_api_key=gemini_api_key)

    # For GET request, just render the form with the API key
    return render_template('create_campaign.html', gemini_api_key=gemini_api_key)


@campaign_bp.route('/preview/<int:campaign_id>', methods=['GET'])
@login_required
def preview_campaign(campaign_id):
    campaign = get_campaign(campaign_id)
    if not campaign:
        flash('Campaign not found', 'error')
        return redirect(url_for('campaign.campaign_list'))

    # Replace merge fields for preview
    body = campaign.get('body', '').replace('{{First Name}}', 'John').replace('{{Last Name}}', 'Doe').replace('{{Email}}', 'john.doe@example.com').replace('{{Company}}', 'Example Corp')
    return render_template('preview_campaign.html', campaign=campaign, body=body)