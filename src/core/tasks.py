from .celery import app


@app.task
def send_email():
    print('Test wysyłki e-mail.')
    return 'XYZ'

@app.task
def generate_monthly_report():
    return "REPORT"