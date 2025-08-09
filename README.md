Heartbeat Monitor

A Python-based network monitor that pings devices on a schedule, logs results, and sends email alerts
when hosts go down, hourly re-alerts while still down, and an all-clear when they recover.
Features
- Checks hosts every 15 minutes (configurable) - Per-host state tracking (up/down) - Hourly re-alerts
while down - All-clear email notifications when recovered - Daily log rotation (14-day retention) -
Optional weekly test email via cron

Requirements

- Python 3.9+ - Virtual environment recommended - Dependencies: ping3 PyYAML - emailutil.py —
included below (edit with your SMTP settings in config.yaml)

Setup:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


Usage:
Run the monitor:
python3 Heartmonitorv1.py
Send a test email:
python3 main.py --test-email
Stop the monitor:
Press Ctrl + C in the terminal.


Deployment
- LAN monitoring: add local IPs to config.yaml - External monitoring: deploy to a VPS or remote server,
add public IP or DDNS hostname to config.yaml - Optional: run via systemd for 24/7 service or cron for
weekly test email
Example config.yaml
instance: "LAN-monitor"


servers:
- name: Core Switch
host: 10.99.97.2
- name: Router WAN
host: myhouse.ddns.net
email:
to: you@example.com
from: alerts@example.com
smtp_server: smtp.example.com
smtp_port: 587
username: smtp-user
password: smtp-password
Example emailutil.py
import smtplib
from email.mime.text import MIMEText
def send_email(subject, body, cfg):
"""Send an email using the settings in config.yaml -> email section."""
msg = MIMEText(body)
msg["Subject"] = subject
msg["From"] = cfg["from"]
msg["To"] = cfg["to"]
try:
with smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"]) as server:
server.starttls()
server.login(cfg["username"], cfg["password"])
server.send_message(msg)
return True
except Exception as e:
print(f"■ Email send failed: {e}")
return False
