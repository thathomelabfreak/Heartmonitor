import smtplib
from email.mime.text import MIMEText

def send_email(subject, body, config):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = config["sender"]
    msg["To"] = config["recipient"]

    with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
        server.starttls()
        server.login(config["sender"], config["password"])
        server.send_message(msg)
