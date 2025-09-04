import csv
import io
from app.utils.email_validator import check_email
import logging

logger = logging.getLogger(__name__)

def validate_csv_data(csv_file):
    """
    Reads a CSV file and validates every row.
    It does NOT save to the database. It only checks for validity.

    Returns:
        A tuple: (is_valid, data_or_errors)
        - If all rows are valid: (True, list_of_contact_dictionaries)
        - If any row is invalid: (False, list_of_error_messages)
    """
    contacts_to_save = []
    errors = []
    
    # Use a copy of the stream so it can be read again if needed
    try:
        file_content = csv_file.stream.read().decode('utf-8-sig')
        csv_file.stream.seek(0) # Reset stream pointer
        text_stream = io.StringIO(file_content)
    except Exception as e:
        return False, [f"Error reading file: {e}"]

    reader = csv.DictReader(text_stream)

    for row_num, row in enumerate(reader, start=2):
        name = row.get('name', '').strip()
        email = row.get('email', '').strip()

        # --- VALIDATION LOGIC ---
        if not name or not email:
            errors.append(f"Row {row_num}: Name or Email is blank.")
            continue # Find all errors, don't stop at the first one

        if not check_email(email):
            errors.append(f"Row {row_num}: Email '{email}' is not a valid format.")
            continue

        # If valid, add the data to our list
        contact_data = {
            'name': name,
            'email': email,
            'location': row.get('location', '').strip(),
            'company_name': row.get('company_name', '').strip()
        }
        contacts_to_save.append(contact_data)
    
    # If we found any errors during the process, the file is invalid
    if errors:
        return False, errors

    return True, contacts_to_save