import os
from pathlib import Path
import sys
import time
from datetime import datetime, timedelta
import yaml
import logging
from logging.handlers import TimedRotatingFileHandler
from ping3 import ping
from emailutil import send_email  # your helper

print("Current working directory:", os.getcwd())

CONFIG_PATH = Path(__file__).parent / "config.yaml"
print("Config path I'm using:", CONFIG_PATH)

# --- Settings ---
CHECK_INTERVAL = 15 * 60       # 15 minutes (seconds)
REALERT_INTERVAL = 60 * 60     # 1 hour (seconds)

# --- Logging: rotate daily, keep 14 days ---
log_handler = TimedRotatingFileHandler("server_check.log", when="midnight", backupCount=14)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[log_handler, logging.StreamHandler(sys.stdout)]
)

def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config not found at {CONFIG_PATH}")
    with CONFIG_PATH.open("r") as f:
        return yaml.safe_load(f)

def check_ping(host):
    # Works on Linux; on macOS, fall back if raw ICMP requires privileges
    try:
        return ping(host, timeout=2) is not None
    except PermissionError:
        if sys.platform == "darwin":
            try:
                return ping(host, timeout=2, privileged=False) is not None
            except TypeError:
                return False
        return False

def send_alert_email(server_name, host, email_cfg):
    subject = f"[ALERT] {server_name} ({host}) is DOWN"
    body = f"{server_name} ({host}) is not responding to ping as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
    try:
        send_email(subject, body, email_cfg)
        logging.info(f"Sent ALERT email for {server_name} ({host})")
        return True
    except Exception as e:
        logging.error(f"Failed to send ALERT email for {server_name} ({host}): {e}")
        return False

def send_clear_email(server_name, host, email_cfg):
    subject = f"[RESOLVED] {server_name} ({host}) is UP"
    body = f"{server_name} ({host}) is responding again as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
    try:
        send_email(subject, body, email_cfg)
        logging.info(f"Sent CLEAR email for {server_name} ({host})")
        return True
    except Exception as e:
        logging.error(f"Failed to send CLEAR email for {server_name} ({host}): {e}")
        return False

def run_loop():
    config = load_config()
    email_cfg = config["email"]

    # State: per host => {"down": bool, "last_alert": datetime|None}
    state = {
        s["host"]: {"name": s["name"], "down": False, "last_alert": None}
        for s in config["servers"]
    }

    logging.info("Heartbeat monitor started. Interval=15m, re-alert=1h.")

    try:
        while True:
            cycle_start = datetime.now()
            for server in config["servers"]:
                name = server["name"]
                host = server["host"]

                up = check_ping(host)
                if up:
                    if state[host]["down"]:
                        # Transition: DOWN -> UP (send clear)
                        logging.warning(f"{name} ({host}) RECOVERED")
                        send_clear_email(name, host, email_cfg)
                        state[host]["down"] = False
                        state[host]["last_alert"] = None
                    else:
                        logging.info(f"{name} ({host}) OK")
                else:
                    if not state[host]["down"]:
                        # Transition: UP -> DOWN (send immediate alert)
                        logging.warning(f"{name} ({host}) DOWN")
                        send_alert_email(name, host, email_cfg)
                        state[host]["down"] = True
                        state[host]["last_alert"] = datetime.now()
                    else:
                        # Still DOWN: send re-alert hourly
                        last = state[host]["last_alert"]
                        if last is None or (datetime.now() - last) >= timedelta(seconds=REALERT_INTERVAL):
                            logging.warning(f"{name} ({host}) still DOWN (hourly re-alert)")
                            sent = send_alert_email(name, host, email_cfg)
                            if sent:
                                state[host]["last_alert"] = datetime.now()

            # Sleep until 15 minutes have passed since cycle start
            elapsed = (datetime.now() - cycle_start).total_seconds()
            sleep_for = max(0, CHECK_INTERVAL - elapsed)
            time.sleep(sleep_for)

    except KeyboardInterrupt:
        logging.info("Heartbeat monitor stopped by user.")

# ...everything above stays the same (imports, settings, functions)...

def send_test_email():
    """Send a test email to verify SMTP works."""
    config = load_config()
    email_cfg = config["email"]
    subject = "[TEST] Heartbeat Monitor Email Check"
    body = "This is a test email from the Heartbeat Monitor script."
    try:
        send_email(subject, body, email_cfg)
        logging.info("Test email sent successfully.")
        print("Test email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send test email: {e}")
        print(f"Failed to send test email: {e}")

if __name__ == "__main__":
    if "--test-email" in sys.argv:
        send_test_email()
    else:
        run_loop()