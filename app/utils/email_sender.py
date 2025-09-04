import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email(config, recipient_email, subject, html_body, in_reply_to=None, references=None):
    host, port, username, password, from_email = config['host'], config['port'], config['username'], config['password'], config['from_email']
    from_name = config.get('from_name')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f'"{from_name}" <{from_email}>' if from_name else from_email
    msg['To'] = recipient_email
    msg['Message-ID'] = make_msgid(domain='sminetechsol.com')

    if in_reply_to:
        msg['In-Reply-To'] = in_reply_to
    if references:
        msg['References'] = references

    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        with smtplib.SMTP_SSL(host, port, timeout=10) if config.get('use_ssl') else smtplib.SMTP(host, port, timeout=10) as server:
            if not config.get('use_ssl') and config.get('use_tls', True):
                server.starttls()
            server.login(username, password)
            server.sendmail(from_email, recipient_email, msg.as_string())
        
        # Return ID, headers, and the full body for logging
        return msg['Message-ID'], msg.get('References'), html_body
    except Exception as e:
        logger.error(f"Failed to send email via SMTP to {recipient_email}: {e}")
        return None, None, None