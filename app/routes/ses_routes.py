from flask import Blueprint, request, render_template, jsonify
from app.models.ses_config import save_ses_config, get_ses_configs
from app.utils.email_validator import check_email
import boto3
from botocore.exceptions import ClientError
import logging

# Configure logging for production
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ses_bp = Blueprint('ses', __name__)

@ses_bp.route('/configure', methods=['GET', 'POST'])
def configure_ses():
    if request.method == 'POST':
        try:
            data = request.form
            aws_access_key_id = data.get('aws_access_key_id')
            aws_secret_access_key = data.get('aws_secret_access_key')
            aws_region = data.get('aws_region')
            sender_email = data.get('sender_email')

            # Validate inputs
            if not all([aws_access_key_id, aws_secret_access_key, aws_region, sender_email]):
                logger.error("Missing required form fields")
                return jsonify({'error': 'All fields are required'}), 400

            # Validate email format
            if not check_email(sender_email):
                logger.error(f"Invalid email format: {sender_email}")
                return jsonify({'error': 'Invalid email format'}), 400

            # Verify AWS SES credentials
            try:
                ses_client = boto3.client(
                    'ses',
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=aws_region
                )
                ses_client.get_send_quota()  # Test credentials
            except ClientError as e:
                logger.error(f"Invalid AWS SES credentials: {str(e)}")
                return jsonify({'error': f'Invalid AWS SES credentials: {str(e)}'}), 400

            # Save to database
            if save_ses_config(aws_access_key_id, aws_secret_access_key, aws_region, sender_email):
                logger.info("SES configuration saved successfully")
                return jsonify({'message': 'SES configuration saved successfully'}), 200
            else:
                logger.error("Failed to save SES configuration to database")
                return jsonify({'error': 'Failed to save SES configuration'}), 500

        except Exception as e:
            logger.error(f"Unexpected error in configure_ses: {str(e)}")
            return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

    configs = get_ses_configs()
    return render_template('index.html', configs=configs)