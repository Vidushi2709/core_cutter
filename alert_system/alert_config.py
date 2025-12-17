"""
Alert Configuration
Configure notification settings for the alert system.
"""
import sys
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for backend imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.configerations import (
    HIGH_IMBALANCE_KW,
    CRITICAL_IMBALANCE_KW,
    OVERVOLTAGE_THRESHOLD,
    UNDERVOLTAGE_THRESHOLD,
    DATA_DIR
)

# Alert thresholds (uses same values from configerations.py)
ALERT_HIGH_IMBALANCE_KW = HIGH_IMBALANCE_KW      # 0.15 kW - triggers warning alerts
ALERT_CRITICAL_IMBALANCE_KW = CRITICAL_IMBALANCE_KW   # 0.6 kW - triggers critical alerts

# Alert throttling - prevent spam
MIN_ALERT_GAP_MINUTES = 5           # Minimum time between alerts of same type
ALERT_REPEAT_INTERVAL_MINUTES = 30  # Repeat critical alerts if not resolved

# Email settings (SMTP)
EMAIL_ENABLED = False
EMAIL_SMTP_HOST = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587
EMAIL_SMTP_USER = "vidushianand09@gmail.com"  # Your email
EMAIL_SMTP_PASSWORD = "your-app-password"  # ⚠️ UPDATE THIS: Get from https://myaccount.google.com/apppasswords
EMAIL_USE_TLS = True

# Engineer contact
ENGINEER_EMAIL = "vidushianand09@gmail.com"  # Alert recipient
ENGINEER_NAME = "Main Engineer"

# CC recipients for alerts
ALERT_CC_EMAILS = [
    # "supervisor@company.com",
    # "backup-engineer@company.com"
]

# SMS settings (using Twilio as example)
SMS_ENABLED = os.getenv("SMS_ENABLED", "False").lower() == "true"
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")  # Get from twilio.com
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")    # Get from twilio.com
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")  # Your Twilio phone number
ENGINEER_PHONE = os.getenv("ENGINEER_PHONE", "")          # Your phone number

# Webhook settings (for integration with Slack, Discord, Teams, etc.)
WEBHOOK_ENABLED = False
WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
WEBHOOK_TYPE = "slack"  # Options: "slack", "discord", "teams", "generic"

# Alert storage
ALERTS_DB = DATA_DIR / "alerts.json"

# Alert message templates
ALERT_TEMPLATES = {
    "critical_imbalance": {
        "subject": "🚨 CRITICAL: Phase Imbalance Detected - {imbalance:.2f} kW",
        "body": """
CRITICAL ALERT - Phase Balancing System

Imbalance Level: {imbalance:.2f} kW (Critical threshold: {threshold:.2f} kW)
System Mode: {mode}
Timestamp: {timestamp}

Phase Status:
{phase_details}

Action Required:
The system is experiencing critical phase imbalance. Automatic balancing may not be 
sufficient. Please review the system immediately.

Dashboard: http://localhost:8000
        """,
    },
    "high_imbalance": {
        "subject": "⚠️ WARNING: High Phase Imbalance - {imbalance:.2f} kW",
        "body": """
WARNING ALERT - Phase Balancing System

Imbalance Level: {imbalance:.2f} kW (Warning threshold: {threshold:.2f} kW)
System Mode: {mode}
Timestamp: {timestamp}

Phase Status:
{phase_details}

The system is attempting automatic balancing. Monitor the situation.

Dashboard: http://localhost:8000
        """,
    },
    "imbalance_resolved": {
        "subject": "✅ RESOLVED: Phase Imbalance Corrected",
        "body": """
RESOLUTION - Phase Balancing System

The phase imbalance has been resolved.

Current Imbalance: {imbalance:.2f} kW
System Mode: {mode}
Timestamp: {timestamp}

Phase Status:
{phase_details}

Dashboard: http://localhost:8000
        """,
    },
    "voltage_issue": {
        "subject": "⚠️ Voltage Issue Detected - Phase {phase}",
        "body": """
VOLTAGE ALERT - Phase Balancing System

Issue Type: {issue_type}
Affected Phase: {phase}
Voltage: {voltage:.1f}V
Threshold: {threshold:.1f}V
Timestamp: {timestamp}

Action may be required to prevent equipment damage.

Dashboard: http://localhost:8000
        """,
    },
}
