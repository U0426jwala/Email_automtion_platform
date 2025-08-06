import os

class Config:
    """
    Application configuration class.
    Loads secrets from environment variables.
    Provides sensible defaults for development.
    """
    # --- Secrets - MUST be set in the .env file ---
    # Fallback key is for local development convenience ONLY.
    # A real SECRET_KEY MUST be set in the environment for production.
    SECRET_KEY = os.getenv('SECRET_KEY') or 'a-temporary-and-insecure-development-key'
    
    # These will be None if not set in the environment, causing an error
    # which is GOOD. It forces you to set them.
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    SES_ACCESS_KEY = os.getenv('SES_ACCESS_KEY')
    SES_SECRET_KEY = os.getenv('SES_SECRET_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    # --- Database and Service Configs ---
    # Defaults are provided for easy local development setup.
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_DB = os.getenv('MYSQL_DB', 'email_automation_db')
    SES_REGION = os.getenv('SES_REGION', 'us-east-1')
