import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import database
import config
from celery_app import celery
from datetime import datetime, timedelta
import logging
from itsdangerous import URLSafeTimedSerializer # Import serializer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create serializer instance (matches the one in completion_server.py)
serializer = URLSafeTimedSerializer(config.FLASK_SECRET_KEY, salt='reminder-completion-salt')

@celery.task(name='tasks.send_reminder_email')
def send_reminder_email(reminder_id):
    """
    Fetches reminder details and sends an email notification.
    """
    conn = None
    try:
        conn = database.sqlite3.connect(database.DATABASE_NAME)
        cursor = conn.cursor()
        # Fetch reminder details including client email if available
        cursor.execute("""
            SELECT r.id, r.due_date, r.reminder_time, r.frequency, r.description, r.is_completed, c.name, c.email
            FROM reminders r
            LEFT JOIN clients c ON r.client_id = c.id
            WHERE r.id = ?
        """, (reminder_id,))
        reminder = cursor.fetchone()
        conn.close() # Close connection after fetching

        if not reminder:
            logging.error(f"Reminder with ID {reminder_id} not found.")
            return f"Reminder {reminder_id} not found."

        rem_id, due_date, reminder_time, frequency, description, is_completed, client_name, client_email = reminder

        if is_completed:
            logging.info(f"Reminder ID {rem_id} is already marked as completed. Skipping email.")
            return f"Reminder {rem_id} already completed."

        if not client_email:
            logging.warning(f"No email address found for client associated with reminder ID {rem_id}. Cannot send email.")
            # Optionally, update reminder status or log differently
            return f"No client email for reminder {rem_id}."

        # --- Email Sending Logic ---
        sender_email = config.EMAIL_HOST_USER
        receiver_email = client_email
        password = config.EMAIL_HOST_PASSWORD

        message = MIMEMultipart("alternative")
        message["Subject"] = f"Reminder: {description} Due on {due_date}"
        message["From"] = sender_email
        message["To"] = receiver_email

        # --- Generate Completion Link ---
        try:
            # Create a signed token containing the reminder ID
            completion_token = serializer.dumps(rem_id)
            completion_link = f"{config.COMPLETION_SERVER_URL}/complete/{completion_token}"
            logging.info(f"Generated completion link for reminder {rem_id}: {completion_link}")
        except Exception as e:
            logging.error(f"Failed to generate completion token for reminder {rem_id}: {e}")
            # Decide how to handle this - maybe send email without link or fail task?
            # For now, let's proceed without the link if generation fails
            completion_link = None

        # --- Create Email Content ---
        text = f"""
        Hi {client_name or 'Client'},

        This is a reminder regarding: {description}
        Due Date: {due_date} at {reminder_time or 'any time'}

        Please ensure this is addressed promptly.

        If this task is completed, please click the link below:
        {completion_link if completion_link else '(Completion link generation failed)'}

        Thank you,
        FinIQ System
        """

        html = f"""
        <html>
        <head>
            <style>
                .button {{
                    display: inline-block;
                    padding: 10px 20px;
                    font-size: 16px;
                    color: white;
                    background-color: #007bff;
                    text-decoration: none;
                    border-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <p>Hi {client_name or 'Client'},</p>
            <p>This is a reminder regarding: <strong>{description}</strong></p>
            <p>Due Date: <strong>{due_date} at {reminder_time or 'any time'}</strong></p>
            <p>Please ensure this is addressed promptly.</p>
            <br>
            <p>If this task is completed, please click the button below:</p>
            {'<a href="' + completion_link + '" class="button">Mark as Completed</a>' if completion_link else '<p>(Completion link generation failed)</p>'}
            <br><br>
            <p>Thank you,<br>FinIQ System</p>
        </body>
        </html>
        """

        # Turn these into plain/html MIMEText objects
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        message.attach(part1)
        message.attach(part2)

        # Send the email
        try:
            context = smtplib.ssl.create_default_context()
            with smtplib.SMTP(config.EMAIL_HOST, config.EMAIL_PORT) as server:
                if config.EMAIL_USE_TLS:
                    server.starttls(context=context)
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
            logging.info(f"Successfully sent reminder email for reminder ID {rem_id} to {receiver_email}")

            # Update last_sent_at timestamp in the database
            try:
                database.update_reminder_last_sent(rem_id, datetime.now(celery.conf.timezone))
                logging.info(f"Updated last_sent_at for reminder ID {rem_id}")
            except Exception as db_update_err:
                logging.error(f"Failed to update last_sent_at for reminder ID {rem_id}: {db_update_err}")
                # Decide if this failure should prevent marking the task as successful

            return f"Email sent for reminder {rem_id}."
        except smtplib.SMTPAuthenticationError:
            logging.error(f"SMTP Authentication Error for reminder ID {rem_id}. Check email credentials in .env.")
            # Consider re-queueing or marking as failed
            raise # Re-raise to let Celery handle retry/failure
        except Exception as e:
            logging.error(f"Failed to send email for reminder ID {rem_id}: {e}")
            # Consider re-queueing or marking as failed
            raise # Re-raise to let Celery handle retry/failure

    except sqlite3.Error as e:
        logging.error(f"Database error processing reminder ID {reminder_id}: {e}")
        # Handle database errors appropriately
        return f"Database error for reminder {reminder_id}."
    except Exception as e:
        logging.error(f"Unexpected error processing reminder ID {reminder_id}: {e}")
        raise # Re-raise for Celery
    finally:
        if conn:
            conn.close()


# --- Task to Periodically Check Reminders (Celery Beat) ---

@celery.task(name='tasks.check_and_schedule_reminders')
def check_and_schedule_reminders():
    """
    Checks the database for reminders that are due and schedules email tasks.
    This task will be run periodically by Celery Beat.
    """
    conn = None
    try:
        conn = database.sqlite3.connect(database.DATABASE_NAME)
        cursor = conn.cursor()

        # Get current date and time in the correct timezone
        now = datetime.now(celery.conf.timezone)
        current_date_str = now.strftime("%Y-%m-%d")
        current_time_str = now.strftime("%H:%M")

        logging.info(f"Checking reminders for {current_date_str} {current_time_str}")

        # Fetch reminders that are due, not completed, and have a client email
        cursor.execute("""
            SELECT r.id, r.due_date, r.reminder_time, r.frequency, r.last_sent_at
            FROM reminders r
            JOIN clients c ON r.client_id = c.id
            WHERE r.is_completed = FALSE
              AND c.email IS NOT NULL AND c.email != ''
        """)

        reminders_to_process = cursor.fetchall()
        conn.close() # Close connection after fetching

        scheduled_count = 0
        for rem_id, due_date_str, reminder_time_str, frequency, last_sent_at_str in reminders_to_process:
            try:
                # Combine date and time, handle potential None for time
                reminder_datetime_str = f"{due_date_str} {reminder_time_str or '00:00'}"
                # Attempt to parse the combined datetime string
                reminder_dt = datetime.strptime(reminder_datetime_str, "%Y-%m-%d %H:%M")
                # Make it timezone aware using Celery's configured timezone
                reminder_dt = celery.conf.timezone.localize(reminder_dt)

                # Parse last_sent_at if it exists
                last_sent_dt = None
                if last_sent_at_str:
                    try:
                        # Parse ISO format string back to datetime
                        last_sent_dt = datetime.fromisoformat(last_sent_at_str)
                        # Ensure it's timezone aware for comparison
                        if last_sent_dt.tzinfo is None:
                             last_sent_dt = celery.conf.timezone.localize(last_sent_dt) # Assume stored in local TZ if naive
                    except ValueError:
                        logging.warning(f"Could not parse last_sent_at '{last_sent_at_str}' for reminder {rem_id}")

                # --- Frequency Logic ---
                should_send = False
                if now >= reminder_dt: # Check if the due date/time has passed
                    if frequency == "Once":
                        if not last_sent_dt: # Send only if never sent before
                            should_send = True
                    elif frequency == "Daily":
                        # Send if never sent or last sent before today
                        if not last_sent_dt or last_sent_dt.date() < now.date():
                            should_send = True
                    elif frequency == "Weekly":
                        # Send if never sent or last sent more than 7 days ago
                        if not last_sent_dt or (now - last_sent_dt) >= timedelta(days=7):
                            should_send = True
                    elif frequency == "Monthly":
                        # Send if never sent or last sent more than ~30 days ago (approximate)
                        # More precise logic would involve calendar month checks
                        if not last_sent_dt or (now - last_sent_dt) >= timedelta(days=30):
                            should_send = True
                    # Add more frequencies if needed

                if should_send:
                    logging.info(f"Scheduling email for reminder ID {rem_id} (Due: {due_date_str} {reminder_time_str}, Freq: {frequency})")
                    send_reminder_email.delay(rem_id) # Queue the email sending task
                    scheduled_count += 1
                # else:
                #     logging.debug(f"Skipping reminder ID {rem_id} based on frequency '{frequency}' and last sent '{last_sent_at_str}'")

            except ValueError as ve:
                logging.error(f"Could not parse date/time for reminder {rem_id}: {due_date_str} {reminder_time_str} - {ve}")
            except Exception as e:
                 logging.error(f"Error processing reminder {rem_id}: {e}")


        logging.info(f"Finished checking reminders. Scheduled {scheduled_count} emails.")
        return f"Checked reminders, scheduled {scheduled_count}."

    except sqlite3.Error as e:
        logging.error(f"Database error checking reminders: {e}")
        return "Database error during check."
    except Exception as e:
        logging.error(f"Unexpected error checking reminders: {e}")
        return "Unexpected error during check."
    finally:
        if conn:
            conn.close()