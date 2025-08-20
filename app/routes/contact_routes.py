from flask import (Blueprint, render_template, request, flash, redirect, url_for,
                   jsonify, send_from_directory)
from flask_login import login_required, current_user
from app.models.contact import (
    create_list, save_contact, get_lists, get_contacts_for_list,
    update_list_records_count, delete_contact_by_id, get_list_by_id,
    delete_list_by_id
)
from app.utils.csv_processor import process_csv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

contact_bp = Blueprint('contact', __name__)

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

@contact_bp.route('/upload_contacts', methods=['POST'])
@login_required
def upload_contacts_file():
    list_name = request.form.get('list_name')
    csv_file = request.files.get('file')

    if not list_name or not csv_file:
        return jsonify({'message': 'List name and CSV file are required.'}), 400

    list_id = create_list(list_name, current_user.id)
    if not list_id:
        return jsonify({'message': 'Failed to create list. A list with this name may already exist.'}), 400

    try:
        saved, skipped, errors = process_csv(csv_file, list_id)
        update_list_records_count(list_id)
        
        message = f"Uploaded {saved} contacts. Skipped {skipped} duplicates."
        if errors:
            message += f" Encountered {len(errors)} errors."

        return jsonify({'message': message}), 200

    except Exception as e:
        logger.error(f"Error during CSV processing: {e}")
        return jsonify({'message': f"An unexpected error occurred: {e}"}), 500

@contact_bp.route('/add_contact/<int:list_id>', methods=['GET', 'POST'])
@login_required
def add_contact(list_id):
    list_details = get_list_by_id(list_id)
    if not list_details:
        flash('The requested list does not exist.', 'error')
        return redirect(url_for('contact.lists'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        location = request.form.get('location')
        company_name = request.form.get('company_name')

        if not name or not email:
            flash('Name and Email are required fields.', 'error')
        elif save_contact(list_id, name, email, location, company_name):
            update_list_records_count(list_id)
            flash(f"Contact '{name}' added successfully!", 'success')
            return redirect(url_for('contact.view_contacts', list_id=list_id))
        else:
            flash('Failed to add contact. The email might already exist.', 'error')

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