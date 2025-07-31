import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_csv(file):
    """
    Processes an uploaded CSV or XLSX file, reads its content, and extracts required contact data.
    Expected columns: 'name', 'email', 'location', 'company_name'.
    """
    try:
        file_extension = file.filename.split('.')[-1].lower()

        if file_extension == 'csv':
            df = pd.read_csv(file)
        elif file_extension == 'xlsx':
            df = pd.read_excel(file)
        else:
            raise ValueError("Unsupported file type. Please upload a CSV or XLSX file.")
        
        required_columns = ['name', 'email', 'location', 'company_name']
        
        # Check if all required columns are present (case-insensitive check for robustness)
        df_columns_lower = [col.lower() for col in df.columns]
        missing_columns = [col for col in required_columns if col not in df_columns_lower]

        if missing_columns:
            raise ValueError(f"File is missing the following required columns: {', '.join(missing_columns)}. "
                             f"Found columns: {', '.join(df.columns)}")

        # Map actual column names to expected lowercase names
        column_mapping = {col.lower(): col for col in df.columns}
        
        # Select and reorder columns based on required_columns
        extracted_data = []
        for index, row in df.iterrows():
            name = row[column_mapping.get('name', '')] if 'name' in column_mapping else ''
            email = row[column_mapping.get('email', '')] if 'email' in column_mapping else ''
            location = row[column_mapping.get('location', '')] if 'location' in column_mapping else ''
            company_name = row[column_mapping.get('company_name', '')] if 'company_name' in column_mapping else ''
            
            # Ensure no None values for database insertion and strip whitespace
            name = str(name).strip() if pd.notna(name) else ''
            email = str(email).strip() if pd.notna(email) else ''
            location = str(location).strip() if pd.notna(location) else ''
            company_name = str(company_name).strip() if pd.notna(company_name) else ''

            # Basic email validation (can be enhanced)
            if not email:
                logger.warning(f"Skipping row {index+2} due to missing email: {row.to_dict()}")
                continue
            # You might want to add more robust email validation here, e.g., using a regex or a library

            extracted_data.append((name, email, location, company_name))
            
        logger.info(f"Successfully processed file, extracted {len(extracted_data)} records.")
        return extracted_data
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise ValueError(f"Failed to process file: {e}")

