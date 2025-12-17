"""Test SMS sending directly"""
from twilio.rest import Client
import os
from dotenv import load_dotenv

# Load credentials from environment variables
load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "your_account_sid_here")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your_auth_token_here")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "+1234567890")
ENGINEER_PHONE = os.getenv("ENGINEER_PHONE", "+1234567890")

try:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    # Test with SHORT message like the real alerts will be
    message = client.messages.create(
        body="ALERT: Phase imbalance 5.2kW detected. Check dashboard.",
        from_=TWILIO_FROM_NUMBER,
        to=ENGINEER_PHONE
    )
    
    print(f"✓ SMS sent successfully!")
    print(f"  Message SID: {message.sid}")
    print(f"  Status: {message.status}")
    print(f"  Segments: {message.num_segments}")
    print(f"  To: {ENGINEER_PHONE}")
    print(f"  Message: ALERT: Phase imbalance 5.2kW detected. Check dashboard.")
    print(f"\nThis is a short message (1 segment). Check your phone!")
    
except Exception as e:
    print(f"✗ Error sending SMS: {e}")
