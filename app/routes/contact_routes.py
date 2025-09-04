from flask import (Blueprint, render_template, request, flash, redirect, url_for,
                   jsonify, send_from_directory)
from flask_login import login_required, current_user
from app.models.contact import (
    create_list, save_contact, get_lists, get_contacts_for_list,
    update_list_records_count, delete_contact_by_id, get_list_by_id,
    delete_list_by_id
)
# --- MODIFICATION START: Import the new validation function ---
from app.utils.csv_processor import validate_csv_data
# --- MODIFICATION END ---
from app.utils.email_validator import check_email
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

contact_bp = Blueprint('contact', __name__)

# ... (keep the other routes like lists, download_sample, delete_list the same) ...
@contact_bp.route('/lists', methods=['GET'])
@login_required
def lists():
    all_lists = get_lists()
    return render_template('upload_contacts.html', lists=all_lists)

@contact_bp.route('/download_sample')
@login_required
def download_sample_csv():
    try:
        return send_from_directory('static/samples', 'Sample_list.csv', as_attachment=True)
    except FileNotFoundError:
        flash('Sample file not found on the server.', 'error')
        return redirect(url_for('contact.lists'))

@contact_bp.route('/delete_list/<int:list_id>', methods=['POST'])
@login_required
def delete_list(list_id):
    list_to_delete = get_list_by_id(list_id)
    if not list_to_delete:
        flash('List not found.', 'error')
        return redirect(url_for('contact.lists'))

    if delete_list_by_id(list_id):
        flash(f"Successfully deleted list '{list_to_delete['list_name']}' and its contacts.", 'success')
    else:
        flash('An error occurred while trying to delete the list.', 'error')

    return redirect(url_for('contact.lists'))

# --- MODIFICATION START: The upload logic is completely new ---
@contact_bp.route('/upload_contacts', methods=['POST'])
@login_required
def upload_contacts_file():
    list_name = request.form.get('list_name')
    csv_file = request.files.get('file')

    if not list_name or not csv_file:
        return jsonify({'message': 'List name and CSV file are required.'}), 400

    # Step 1: Validate the entire CSV file first
    is_valid, data_or_errors = validate_csv_data(csv_file)

    if not is_valid:
        # The file has errors, so reject the upload
        error_message = "Upload failed. Please fix the following errors: " + ", ".join(data_or_errors)
        logger.error(f"CSV Upload Failed for user {current_user.id}: {error_message}")
        return jsonify({'message': error_message}), 400

    # Step 2: If validation passed, create the list
    list_id = create_list(list_name, current_user.id)
    if not list_id:
        return jsonify({'message': 'Failed to create list. A list with this name may already exist.'}), 400

    # Step 3: Save the validated contacts
    saved_count = 0
    skipped_count = 0 # For duplicates
    valid_contacts = data_or_errors # The data is in this variable if validation passed

    for contact_data in valid_contacts:
        if save_contact(list_id, **contact_data):
            saved_count += 1
        else:
            skipped_count += 1 # This contact was a duplicate in the database

    update_list_records_count(list_id)
    
    message = f"Successfully uploaded {saved_count} contacts."
    if skipped_count > 0:
        message += f" Skipped {skipped_count} duplicates."
    
    return jsonify({'message': message}), 200
# --- MODIFICATION END ---


# ... (keep the other routes like add_contact, view_contacts, delete_contact the same) ...
@contact_bp.route('/add_contact/<int:list_id>', methods=['GET', 'POST'])
@login_required
def add_contact(list_id):
    list_details = get_list_by_id(list_id)
    if not list_details:
        flash('The requested list does not exist.', 'error')
        return redirect(url_for('contact.lists'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        location = request.form.get('location')
        company_name = request.form.get('company_name')

        errors = []
        if not name:
            errors.append('Name is a required field.')
        
        if not email:
            errors.append('Email is a required field.')
        elif not check_email(email):
            errors.append('The email address provided is not valid.')

        if errors:
            for error in errors:
                flash(error, 'error')
        elif save_contact(list_id, name, email, location, company_name):
            update_list_records_count(list_id)
            flash(f"Contact '{name}' added successfully!", 'success')
            return redirect(url_for('contact.view_contacts', list_id=list_id))
        else:
            flash('Failed to add contact. The email might already exist in this list.', 'error')

    return render_template('add_contact.html', list_id=list_id, list_details=list_details)

@contact_bp.route('/view_contacts/<int:list_id>', methods=['GET'])
@login_required
def view_contacts(list_id):
    contacts = get_contacts_for_list(list_id)
    list_details = get_list_by_id(list_id)
    if not list_details:
        flash('The requested list does not exist.', 'error')
        return redirect(url_for('contact.lists'))
    return render_template('view_contacts.html', contacts=contacts, list_id=list_id, list_details=list_details)

@contact_bp.route('/delete_contact/<int:list_id>/<int:contact_id>', methods=['POST'])
@login_required
def delete_contact(list_id, contact_id):
    if delete_contact_by_id(contact_id):
        update_list_records_count(list_id)
        flash('Contact deleted successfully.', 'success')
    else:
        flash('Failed to delete contact.', 'error')
    return redirect(url_for('contact.view_contacts', list_id=list_id))