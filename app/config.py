import os

class Config:
    # --- Secrets - MUST be set in environment ---
    SECRET_KEY = os.getenv('SECRET_KEY')
    MYSQL_PASSWORD = os.getenv('DB_PASSWORD')
    SES_ACCESS_KEY = os.getenv('SES_ACCESS_KEY')
    SES_SECRET_KEY = os.getenv('SES_SECRET_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    # --- Non-Secrets - Defaults are OK for local development ---
    MYSQL_HOST = os.getenv('DB_HOST', 'localhost')
    MYSQL_USER = os.getenv('DB_USER', 'root')
    MYSQL_DB = os.getenv('DB_NAME', 'email_automation_db')
    SES_REGION = os.getenv('SES_REGION', 'us-east-1')