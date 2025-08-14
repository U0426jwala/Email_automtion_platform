import os

class Config:
    """
    Application configuration class.
    Loads secrets from environment variables.
    Provides sensible defaults for development.
    """
    # --- Secrets - MUST be set in the .env file ---
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-temporary-and-insecure-development-key')
    
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    # --- AWS Credentials and Configs ---
    # Using standard Boto3 environment variable names for better compatibility.
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    # CORRECTED: Renamed from SES_REGION to match email_sender.py
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # ADDED: This was missing but is required by email_sender.py
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')

    # --- Database Configs with Defaults ---
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_DB = os.getenv('MYSQL_DB', 'email_automation_db')