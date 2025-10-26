from .celery import app


@app.task
def send_email():
    from django.core.mail import send_mail
    print('Test wysyłki e-mail.')
    return 'XYZ'

@app.task
def generate_monthly_report():
    return "REPORT"