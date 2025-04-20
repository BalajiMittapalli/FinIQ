from flask import Flask, request, render_template_string, abort
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import database
import config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY

# Create a serializer object with the secret key and salt
# Salt adds an extra layer of security specific to this use case
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'], salt='reminder-completion-salt')

# Simple HTML templates for responses
SUCCESS_TEMPLATE = """
<!doctype html>
<title>Reminder Completed</title>
<h1>Reminder Marked as Completed</h1>
<p>Thank you! The reminder has been successfully marked as completed.</p>
"""

ERROR_TEMPLATE = """
<!doctype html>
<title>Error</title>
<h1>Error</h1>
<p>{{ message }}</p>
"""

EXPIRED_TEMPLATE = """
<!doctype html>
<title>Link Expired</title>
<h1>Link Expired</h1>
<p>This completion link has expired.</p>
"""

INVALID_TEMPLATE = """
<!doctype html>
<title>Invalid Link</title>
<h1>Invalid Link</h1>
<p>This completion link is invalid or has been tampered with.</p>
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@app.route('/test-email')
def test_email():
    try:
        msg = MIMEMultipart()
        msg['Subject'] = 'Test Email from FinIQ'
        msg['From'] = config.EMAIL_HOST_USER
        msg['To'] = config.EMAIL_HOST_USER
        msg.attach(MIMEText('This is a test email from FinIQ system.', 'plain'))

        with smtplib.SMTP(config.EMAIL_HOST, config.EMAIL_PORT) as server:
            if config.EMAIL_USE_TLS:
                server.starttls()
            server.login(config.EMAIL_HOST_USER, config.EMAIL_HOST_PASSWORD)
            server.send_message(msg)

        return 'Test email sent successfully!', 200
    except Exception as e:
        return f'Error sending test email: {str(e)}', 500

@app.route('/complete/<token>')
def complete_reminder(token):
    """
    Handles the reminder completion link clicked from the email.
    Verifies the token and marks the reminder as completed in the database.
    """
    try:
        # Unsign the token, max_age set to 7 days (adjust as needed)
        reminder_id = serializer.loads(token, max_age=60*60*24*7) # 7 days expiry
        logging.info(f"Received completion request for reminder ID: {reminder_id} with token: {token}")

        # Mark the reminder as completed in the database
        try:
            database.mark_reminder_completed(reminder_id)
            logging.info(f"Successfully marked reminder ID {reminder_id} as completed.")
            return render_template_string(SUCCESS_TEMPLATE)
        except Exception as db_err:
            logging.error(f"Database error marking reminder {reminder_id} complete: {db_err}")
            return render_template_string(ERROR_TEMPLATE, message="Could not update reminder status due to a database error."), 500

    except SignatureExpired:
        logging.warning(f"Expired completion token received: {token}")
        return render_template_string(EXPIRED_TEMPLATE), 400
    except BadSignature:
        logging.warning(f"Invalid completion token received: {token}")
        return render_template_string(INVALID_TEMPLATE), 400
    except Exception as e:
        logging.error(f"Unexpected error handling completion token {token}: {e}")
        return render_template_string(ERROR_TEMPLATE, message="An unexpected error occurred."), 500

if __name__ == '__main__':
    # Run the Flask server
    # Use 0.0.0.0 to make it accessible on your network if needed, otherwise 127.0.0.1
    # Debug should be False in production
    logging.info("Starting Flask completion server on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=False)