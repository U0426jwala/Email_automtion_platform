# Email_automation_platform/run.py (Updated)

from dotenv import load_dotenv
load_dotenv() # This line reads your .env file and loads the variables

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)