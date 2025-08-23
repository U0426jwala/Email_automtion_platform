# app/celery_app.py (Corrected)

from celery import Celery
from celery.schedules import crontab

# THE FIX: Create the celery instance globally, but without any configuration.
# The task modules will import this instance to use its decorators.
celery = Celery(__name__, include=['app.utils.email_scheduler'])

def create_celery_app(app=None):
    """
    Configure the global celery instance and tie it to the Flask app's configuration.
    """
    # Use the global celery instance
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        # Add the CELERY_BEAT_SCHEDULE configuration here
        beat_schedule={
            'process-due-steps-every-60-seconds': {
                'task': 'app.utils.email_scheduler.process_due_steps',
                # Set the schedule to run every minute
                'schedule': crontab(minute='*'),
            },
        }
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery