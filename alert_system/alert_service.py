"""
Alert Service
Handles sending alerts via different channels: Email, SMS, and Webhooks.
"""
import smtplib
import json
import re
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, List
from abc import ABC, abstractmethod

from . import alert_config as config


class AlertService(ABC):
    """Base class for alert services."""
    
    @abstractmethod
    def send_alert(self, subject: str, message: str, severity: str = "info") -> bool:
        """Send an alert. Returns True if successful."""
        pass


class EmailAlertService(AlertService):
    """Send alerts via email using SMTP."""
    
    def __init__(self):
        self.enabled = config.EMAIL_ENABLED
        self.smtp_host = config.EMAIL_SMTP_HOST
        self.smtp_port = config.EMAIL_SMTP_PORT
        self.smtp_user = config.EMAIL_SMTP_USER
        self.smtp_password = config.EMAIL_SMTP_PASSWORD
        self.use_tls = config.EMAIL_USE_TLS
        self.from_email = config.EMAIL_SMTP_USER
        self.to_email = config.ENGINEER_EMAIL
        self.cc_emails = config.ALERT_CC_EMAILS
    
    def send_alert(self, subject: str, message: str, severity: str = "info") -> bool:
        """Send email alert."""
        if not self.enabled:
            print(f"[EMAIL] Disabled - Would send: {subject}")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            msg['Subject'] = subject
            
            # Add CC recipients
            if self.cc_emails:
                msg['Cc'] = ', '.join(self.cc_emails)
            
            # Add severity and timestamp to message
            full_message = f"Severity: {severity.upper()}\n"
            full_message += f"Sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            full_message += "\n" + message
            
            msg.attach(MIMEText(full_message, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                
                # Include CC recipients
                recipients = [self.to_email] + self.cc_emails
                server.send_message(msg, to_addrs=recipients)
            
            print(f"[EMAIL] ✓ Sent to {self.to_email}: {subject}")
            return True
            
        except Exception as e:
            print(f"[EMAIL] ✗ Failed to send email: {e}")
            return False


class SMSAlertService(AlertService):
    """Send alerts via SMS using Twilio."""
    
    def __init__(self):
        self.enabled = config.SMS_ENABLED
        if self.enabled:
            try:
                from twilio.rest import Client
                self.client = Client(
                    config.TWILIO_ACCOUNT_SID,
                    config.TWILIO_AUTH_TOKEN
                )
                self.from_number = config.TWILIO_FROM_NUMBER
                self.to_number = config.ENGINEER_PHONE
            except ImportError:
                print("[SMS] Warning: twilio package not installed. Run: pip install twilio")
                self.enabled = False
            except Exception as e:
                print(f"[SMS] Warning: Failed to initialize Twilio: {e}")
                self.enabled = False
    
    def send_alert(self, subject: str, message: str, severity: str = "info") -> bool:
        """Send SMS alert."""
        if not self.enabled:
            print(f"[SMS] Disabled - Would send: {subject}")
            return False
        
        try:
            # SMS messages MUST be under 160 chars (1 segment) for Indian carriers
            # Keep it super simple to avoid rejection
            if "imbalance" in subject.lower():
                # Extract just the kW value from subject
                match = re.search(r'(\d+\.?\d*)\s*kW', subject)
                kw_value = match.group(1) if match else "?"
                sms_message = f"ALERT: Phase imbalance {kw_value}kW detected. Check dashboard."
            elif "voltage" in subject.lower():
                # Extract phase name
                match = re.search(r'Phase\s+(\w+)', subject)
                phase = match.group(1) if match else "?"
                sms_message = f"ALERT: Voltage issue on Phase {phase}. Check system."
            else:
                # Generic short message
                sms_message = f"ALERT: {subject[:100]}"
            
            # Ensure message is under 160 characters
            sms_message = sms_message[:159]
            
            print(f"[SMS DEBUG] Message ({len(sms_message)} chars): {sms_message}")
            
            message_obj = self.client.messages.create(
                body=sms_message,
                from_=self.from_number,
                to=self.to_number
            )
            
            print(f"[SMS] ✓ Sent to {self.to_number}: {message_obj.sid}")
            print(f"[SMS] Status: {message_obj.status}, Segments: {message_obj.num_segments}")
            return True
            
        except Exception as e:
            print(f"[SMS] ✗ Failed to send SMS: {e}")
            return False


class WebhookAlertService(AlertService):
    """Send alerts via webhook (Slack, Discord, Teams, etc.)."""
    
    def __init__(self):
        self.enabled = config.WEBHOOK_ENABLED
        self.webhook_url = config.WEBHOOK_URL
        self.webhook_type = config.WEBHOOK_TYPE
    
    def send_alert(self, subject: str, message: str, severity: str = "info") -> bool:
        """Send webhook alert."""
        if not self.enabled:
            print(f"[WEBHOOK] Disabled - Would send: {subject}")
            return False
        
        try:
            payload = self._build_payload(subject, message, severity)
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 201, 204]:
                print(f"[WEBHOOK] ✓ Sent to {self.webhook_type}: {subject}")
                return True
            else:
                print(f"[WEBHOOK] ✗ Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"[WEBHOOK] ✗ Failed to send webhook: {e}")
            return False
    
    def _build_payload(self, subject: str, message: str, severity: str) -> dict:
        """Build webhook payload based on platform."""
        
        # Color coding by severity
        colors = {
            "critical": "#DC2626",  # Red
            "warning": "#F59E0B",   # Orange
            "info": "#10B981",      # Green
        }
        color = colors.get(severity, colors["info"])
        
        if self.webhook_type == "slack":
            return {
                "text": subject,
                "attachments": [{
                    "color": color,
                    "text": message,
                    "footer": "Phase Balancing System",
                    "ts": int(datetime.now().timestamp())
                }]
            }
        
        elif self.webhook_type == "discord":
            return {
                "content": f"**{subject}**",
                "embeds": [{
                    "description": message,
                    "color": int(color.replace("#", ""), 16),
                    "footer": {"text": "Phase Balancing System"},
                    "timestamp": datetime.now().isoformat()
                }]
            }
        
        elif self.webhook_type == "teams":
            return {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": color,
                "summary": subject,
                "sections": [{
                    "activityTitle": subject,
                    "activitySubtitle": "Phase Balancing System",
                    "text": message,
                    "markdown": True
                }]
            }
        
        else:  # generic
            return {
                "subject": subject,
                "message": message,
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
                "source": "Phase Balancing System"
            }


class MultiChannelAlertService:
    """Coordinates sending alerts across multiple channels."""
    
    def __init__(self):
        self.email_service = EmailAlertService()
        self.sms_service = SMSAlertService()
        self.webhook_service = WebhookAlertService()
    
    def send_alert(
        self,
        subject: str,
        message: str,
        severity: str = "info",
        channels: Optional[List[str]] = None
    ) -> dict:
        """
        Send alert across specified channels.
        
        Args:
            subject: Alert subject/title
            message: Alert message body
            severity: "critical", "warning", or "info"
            channels: List of channels to use. If None, uses all enabled channels.
                     Options: ["email", "sms", "webhook"]
        
        Returns:
            dict with status of each channel
        """
        if channels is None:
            channels = ["email", "sms", "webhook"]
        
        results = {}
        
        if "email" in channels:
            results["email"] = self.email_service.send_alert(subject, message, severity)
        
        if "sms" in channels and severity in ["critical", "warning"]:
            # Only send SMS for important alerts
            results["sms"] = self.sms_service.send_alert(subject, message, severity)
        
        if "webhook" in channels:
            results["webhook"] = self.webhook_service.send_alert(subject, message, severity)
        
        return results
