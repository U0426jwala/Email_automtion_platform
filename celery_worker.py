# celery_worker.py (Updated)

# STEP 1: Apply the eventlet patch.
# This MUST be the first thing to happen.
import eventlet
eventlet.monkey_patch()

# STEP 2: Now import everything else
from dotenv import load_dotenv
load_dotenv()

from app import create_app

# Create the Flask app which in turn creates the Celery app
flask_app = create_app()

# Expose the Celery app instance for the CLI
celery = flask_app.celery