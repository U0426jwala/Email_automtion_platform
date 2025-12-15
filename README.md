Markdown

# 📧 AI-Powered Email Automation Platform

A robust, full-stack email marketing and automation platform built with Python. Designed for high-volume sending, cold outreach sequences, and detailed analytics. It supports SMTP relaying (Amazon SES, SendGrid, etc.), automated follow-up sequences, and AI-assisted content generation.

## 🚀 Key Features

* **Smart Sequences:** Create multi-step drip campaigns that automatically follow up if no reply is detected.
* **Threaded Replies:** Follow-up emails appear in the same thread (Re: Subject) just like a human sent them.
* **Contact Management:** Bulk CSV upload with real-time validation (checks for invalid formats and duplicates).
* **Bounce Handling:** Integrated with AWS SQS to automatically flag and stop sending to bounced emails.
* **Analytics Dashboard:** Visual reports for Sent, Delivered, Bounced, and Scheduled emails.
* **AI Integration:** Uses Google Gemini to help generate or optimize email content.
* **SMTP Agnostic:** Connect multiple SMTP accounts and rotate between them.

## 🛠️ Tech Stack

* **Backend:** Python 3, Flask
* **Database:** MySQL (SQLAlchemy/Connector)
* **Task Queue:** Celery + Redis (for scheduling and background sending)
* **Frontend:** HTML5, Bootstrap, Jinja2 Templates
* **Deployment:** Gunicorn, Systemd, Nginx

## ⚙️ Installation & Setup

### 1. Prerequisites
Ensure you have the following installed on your server:
* Python 3.8+
* MySQL Server
* Redis Server (`sudo apt install redis-server`)

### 2. Clone the Repository
```bash
git clone [https://github.com/yourusername/email-automation-platform.git](https://github.com/yourusername/email-automation-platform.git)
cd email-automation-platform
3. Set Up Virtual Environment
Bash

python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
4. Install Dependencies
Bash

pip install -r requirements.txt
5. Environment Configuration
Create a .env file in the root directory. You can use the example below:

Ini, TOML

# .env file

# Flask Settings
SECRET_KEY=your_very_secret_key_here
FLASK_APP=run.py
FLASK_ENV=production

# Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=your_db_user
MYSQL_PASSWORD=your_db_password
MYSQL_DB=email_platform_db

# Encryption (For storing SMTP passwords securely)
ENCRYPTION_KEY=your_generated_fernet_key_here

# AWS (For Bounce Handling via SQS)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret

# AI Integration
GEMINI_API_KEY=your_google_gemini_key
6. Database Setup
Log into your MySQL console and create the database:

SQL

CREATE DATABASE email_platform_db;
Note: Ensure you import the initial schema schema.sql (if available) or run the migration scripts to create the tables (users, campaigns, contacts, sent_emails, etc.).

🏃‍♂️ Running the Application
Local Development
Start the Redis server: redis-server

Start the Celery worker (in a new terminal):

Bash

celery -A celery_worker.celery worker --loglevel=info
Start the Celery Beat scheduler (in a new terminal):

Bash

celery -A celery_worker.celery beat --loglevel=info
Run the Flask app:

Bash

python run.py
Access the app at http://localhost:5000.

🚀 Production (VPS / DigitalOcean / Hetzner)
For production, do not use python run.py. Instead, use Gunicorn and Systemd.

1. Run Gunicorn:

Bash

gunicorn --workers 3 --bind 0.0.0.0:8000 run:app
2. Daemonize Processes (Systemd): You should create three service files in /etc/systemd/system/:

email-web.service (Runs Gunicorn)

email-worker.service (Runs Celery Worker)

email-beat.service (Runs Celery Beat Scheduler)

Enable them using:

Bash

sudo systemctl start email-web email-worker email-beat
sudo systemctl enable email-web email-worker email-beat
📂 Project Structure
├── app/
│   ├── models/          # Database models (User, Campaign, Sequence, Logs)
│   ├── routes/          # Flask Blueprints (Campaigns, Contacts, SMTP, Reports)
│   ├── templates/       # HTML files (Jinja2)
│   ├── static/          # CSS, JS, Images
│   ├── utils/           # Helpers (Email Sender, CSV Validator, Scheduler)
│   ├── __init__.py      # App Factory
│   ├── celery_app.py    # Celery Configuration
│   └── database.py      # DB Connection logic
├── .env                 # Environment variables (Ignored by Git)
├── config.py            # App Configuration
├── celery_worker.py     # Entry point for Celery
├── requirements.txt     # Python dependencies
├── run.py               # Entry point for Flask
└── README.md            # Project Documentation
🛡️ Security Note
This application uses Fernet symmetric encryption to store SMTP passwords in the database.

Ensure ENCRYPTION_KEY is kept safe. If you lose it, you cannot decrypt stored SMTP credentials.

🤝 Contributing
Fork the Project

Create your Feature Branch (git checkout -b feature/AmazingFeature)

Commit your Changes (git commit -m 'Add some AmazingFeature')

Push to the Branch (git push origin feature/AmazingFeature)

Open a Pull Request

📄 License
Distributed under the MIT License.
