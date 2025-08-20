import pandas as pd
import io
from app.models.contact import save_contact
import logging

logger = logging.getLogger(__name__)

def process_csv(csv_file, list_id):
    """
    Processes an uploaded CSV file to extract and save contact information.

    Args:
        csv_file: The file object from the request.
        list_id: The ID of the contact list to associate contacts with.

    Returns:
        A tuple containing:
        - saved_contacts_count (int): Number of new contacts saved.
        - skipped_contacts_count (int): Number of duplicate or failed contacts.
        - error_contacts (list): A list of error messages, if any.
    """
    saved_contacts_count = 0
    skipped_contacts_count = 0
    error_contacts = []

    try:
        # Read the file content into memory and handle potential byte order marks (BOM)
        content = csv_file.read().decode('utf-8-sig')
        
        # Use the pandas library to read the CSV data from the string
        df = pd.read_csv(io.StringIO(content))

        # Standardize column names to prevent case or spacing issues (e.g., " Name " -> "name")
        df.columns = [col.strip().lower() for col in df.columns]

        # Check for the essential 'email' and 'name' columns
        if 'email' not in df.columns or 'name' not in df.columns:
            raise ValueError("CSV file must contain 'email' and 'name' columns.")

        # Iterate through each row in the CSV data
        for index, row in df.iterrows():
            name = row.get('name')
            email = row.get('email')

            # Handle optional columns safely; they will be None if not found
            location = row.get('location')
            company_name = row.get('company_name')

            # The save_contact function returns True on success, False on failure/duplicate
            if save_contact(list_id, name, email, location, company_name):
                saved_contacts_count += 1
            else:
                skipped_contacts_count += 1
    
    except Exception as e:
        logger.error(f"An error occurred during CSV processing: {e}")
        # Add a user-friendly error message to the list to be displayed
        error_contacts.append(f"Processing failed: {e}")

    return saved_contacts_count, skipped_contacts_count, error_contacts