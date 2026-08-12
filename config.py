import os
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER         = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL    = os.getenv("RECIPIENT_EMAIL")

CHECK_INTERVAL_HOURS  = 1
ALERT_COOLDOWN_HOURS  = 24   # don't re-alert for same product within this window
ALERTS_LOG_FILE       = "alerts_log.json"
