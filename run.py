# run.py

from app import create_app
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Always try to import Waitress, as it's the primary choice for Windows development ---
try:
    from waitress import serve
except ImportError:
    logger.error("Waitress is not installed. Please run 'pip install waitress'.")
    # If Waitress is absolutely required for your development setup on Windows,
    # you might want to exit here, or provide more specific instructions.
    serve = None # Set to None if not available to prevent NameError later


# --- Conditional Import for Gunicorn (only if FLASK_ENV is production and on compatible OS) ---
StandaloneApplication = None # Initialize to None
if os.getenv('FLASK_ENV') == 'production':
    try:
        import gunicorn.app.base
        # Define StandaloneApplication only if gunicorn is available
        class StandaloneApplication(gunicorn.app.base.BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                config = {key: value for key, value in self.options.items()
                          if key in self.cfg.settings and value is not None}
                for key, value in config.items():
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application
    except ImportError:
        logger.warning("Gunicorn not found or not compatible. It will not be used even if FLASK_ENV is production.")
        # StandaloneApplication remains None
    except Exception as e:
        logger.error(f"Error initializing Gunicorn components: {e}")
        # StandaloneApplication remains None


def main():
    try:
        # Create Flask app
        app = create_app()
        logger.info("Flask application created successfully")

        # Check environment
        if os.getenv('FLASK_ENV') == 'production':
            if StandaloneApplication: # Check if Gunicorn class was successfully loaded
                logger.info("Starting Gunicorn server on 0.0.0.0:5000 (Production Environment)")
                options = {
                    'bind': '0.0.0.0:5000',
                    'workers': 4,
                    'timeout': 30,
                    'loglevel': 'info',
                    'capture_output': True, # Capture stdout/stderr to Gunicorn logs
                    'enable_stdio_inheritance': True, # Pass stdin/out to worker processes
                }
                StandaloneApplication(app, options).run()
            else:
                logger.error("Cannot run Gunicorn in production because it's not available or compatible.")
                if serve: # Use Waitress as a fallback if it was imported successfully
                    logger.info("Falling back to Waitress for testing production-like setup on unsupported OS.")
                    serve(app, host='0.0.0.0', port=5000)
                else:
                    logger.critical("No suitable WSGI server found for production environment. Exiting.")
                    exit(1) # Critical error, exit the application
        else:
            if serve: # Use Waitress for development on Windows
                logger.info("Starting Waitress server on http://0.0.0.0:5000 (Development Environment - Windows Compatible)")
                serve(app, host='0.0.0.0', port=5000)
            else:
                # Fallback to Flask's built-in server if Waitress isn't available for development
                logger.warning("Waitress not available. Falling back to Flask development server. NOT for production use.")
                logger.info("Starting Flask development server on http://0.0.0.0:5000 (Development Environment)")
                app.run(debug=True, host="0.0.0.0", port=5000)

    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise # Re-raise the exception after logging for debugging


if __name__ == "__main__":
    main()