# config.py (Updated)

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key'
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'default_user')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'default_db')

    # --- GEMINI API KEY ---
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

    # --- NEW CELERY CONFIGURATION ---
    CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
    CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
