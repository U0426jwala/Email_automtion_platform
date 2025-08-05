import os

class Config:
    # --- Secrets - MUST be set in environment ---
    SECRET_KEY = os.getenv('1482e314a521c481d883e4078c9e9b23')
    MYSQL_PASSWORD = os.getenv('Ujwala@26')
    SES_ACCESS_KEY = os.getenv('AKIAXQIQAJ5BX5MG7TD7')
    SES_SECRET_KEY = os.getenv('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')
    GEMINI_API_KEY = os.getenv('AIzaSyA8ZqXcGH1ZTuzpsaKSTW3lJ8Qb7nIII4o')

    # --- Non-Secrets - Defaults are OK for local development ---
    MYSQL_HOST = os.getenv('DB_HOST', 'localhost')
    MYSQL_USER = os.getenv('DB_USER', 'root')
    MYSQL_DB = os.getenv('DB_NAME', 'email_automation_db')
    SES_REGION = os.getenv('SES_REGION', 'us-east-1')