import os

from celery import Celery

from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery("core")

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.beat_schedule = {
    'monthly-report': {
        'task': 'core.tasks.generate_monthly_report',
        'schedule': 5.0,
    }
}

# crontab(day_of_month=1, hour=9, minute=0)