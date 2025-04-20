from celery import Celery
import config

# Initialize Celery
# The first argument is the name of the current module, important for automatic task discovery.
# The 'broker' and 'backend' arguments specify the message broker (Redis) and result backend.
# 'include' tells Celery where to find task modules.
celery = Celery(
    'fin_iq_tasks',
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
    include=['tasks'] # Look for tasks in tasks.py
)

# Optional configuration settings
celery.conf.update(
    result_expires=3600, # How long to keep task results (in seconds)
    task_serializer='json',
    accept_content=['json'],  # Ensure tasks use JSON serialization
    result_serializer='json',
    timezone='Asia/Calcutta', # Set your timezone
    enable_utc=True,
)

# Configure Celery Beat schedule
celery.conf.beat_schedule = {
    # Executes the check task every 5 minutes (300 seconds)
    'check-reminders-every-5-minutes': {
        'task': 'tasks.check_and_schedule_reminders', # The task defined in tasks.py
        'schedule': 300.0, # Run every 300 seconds (5 minutes)
    },
}

# Optional: Set timezone for Celery Beat
celery.conf.timezone = 'Asia/Calcutta'

if __name__ == '__main__':
    # This is typically used for starting a worker, not the beat scheduler directly.
    # Beat is usually run as a separate process: celery -A celery_app beat -l info
    # Worker is run as: celery -A celery_app worker -l info
    pass # Keep this minimal, starting is done via CLI