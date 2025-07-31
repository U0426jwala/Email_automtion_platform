from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models.contact import create_list, save_contact, get_lists, get_contacts_by_list, update_list_records_count
from app.utils.csv_processor import process_csv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

contact_bp = Blueprint('contact', __name__)

@contact_bp.route('/lists', methods=['GET'])
@login_required
def lists():
    """
    Handles displaying the main contact lists page. The POST logic for creating a
    list from this page has been moved to a dedicated function for clarity.
    """
    all_lists = get_lists()
    return render_template('upload_contacts.html', lists=all_lists)

@contact_bp.route('/create_and_upload', methods=['POST'])
@login_required
def create_and_upload_list():
    """
    Handles creating a new list and uploading contacts from a CSV in a single action.
    This is used by the modal on the 'Create Sequence' page.
    """
    try:
        list_name = request.form.get('list_name')
        file = request.files.get('file')

        if not list_name or not file or not file.filename:
            return jsonify({'status': 'error', 'message': 'List name and a CSV file are required.'}), 400

        if not file.filename.lower().endswith('.csv'):
            return jsonify({'status': 'error', 'message': 'Please upload a valid CSV file.'}), 400
        
        # --- Transactional Logic ---
        # 1. Create a new list
        list_id = create_list(list_name, current_user.username)
        if not list_id:
            return jsonify({'status': 'error', 'message': 'Failed to create the new list in the database.'}), 500

        # 2. Process the CSV and save contacts
        contacts_data = process_csv(file)
        contacts_saved = 0
        for name, email, location, company_name in contacts_data:
            if save_contact(list_id, name, email, location, company_name):
                contacts_saved += 1
            else:
                logger.warning(f"Failed to save contact from CSV: {email}")
        
        # 3. Update the final count
        update_list_records_count(list_id, contacts_saved)

        # 4. Return success with the new list's data
        new_list_data = {
            'id': list_id,
            'list_name': list_name,
            'total_records': contacts_saved
        }

        return jsonify({
            'status': 'success', 
            'message': f"List '{list_name}' created with {contacts_saved} contacts!",
            'list': new_list_data # Send the new list data back to the frontend
        }), 200

    except ValueError as e:
        return jsonify({'status': 'error', 'message': f'CSV processing error: {e}'}), 400
    except Exception as e:
        logger.error(f"Error during list creation and upload: {e}")
        return jsonify({'status': 'error', 'message': f'An unexpected error occurred: {str(e)}'}), 500

# The following routes are for other functionalities and remain unchanged
@contact_bp.route('/add_contact/<int:list_id>', methods=['GET', 'POST'])
@login_required
def add_contact(list_id):
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        location = request.form.get('location')
        company_name = request.form.get('company_name')
        segment = request.form.get('segment')
        if save_contact(list_id, name, email, location, company_name, segment):
            flash(f"Contact '{name}' added successfully!", 'success')
            return redirect(url_for('contact.lists'))
        flash('Failed to add contact.', 'error')
    return render_template('add_contact.html', list_id=list_id)

@contact_bp.route('/view_contacts/<int:list_id>', methods=['GET'])
@login_required
def view_contacts(list_id):
    contacts = get_contacts_by_list(list_id)
    return render_template('view_contacts.html', contacts=contacts, list_id=list_id)