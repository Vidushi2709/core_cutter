"""
Alert Manager
Manages alert logic, throttling, tracking, and history.
"""
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

from . import alert_config as config
from .alert_service import MultiChannelAlertService


@dataclass
class Alert:
    """Represents a single alert event."""
    alert_id: str
    timestamp: str
    alert_type: str  # "critical_imbalance", "high_imbalance", "voltage_issue", etc.
    severity: str    # "critical", "warning", "info"
    subject: str
    message: str
    imbalance_kw: float
    system_mode: str
    phase_details: Dict
    channels_sent: Dict[str, bool]
    resolved: bool = False
    resolved_at: Optional[str] = None


class AlertManager:
    """Manages alert generation, throttling, and history."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or config.ALERTS_DB
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.alert_service = MultiChannelAlertService()
        self.alerts_history: List[Alert] = []
        self.last_alert_times: Dict[str, datetime] = {}
        self.active_alerts: Dict[str, Alert] = {}  # Track unresolved alerts
        
        self._load_history()
    
    def _load_history(self):
        """Load alert history from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.alerts_history = [
                        Alert(**alert) for alert in data.get('alerts', [])
                    ]
                    
                    # Rebuild last_alert_times from recent history
                    now = datetime.now(timezone.utc)
                    for alert in self.alerts_history[-50:]:  # Last 50 alerts
                        alert_time = datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00'))
                        if (now - alert_time).total_seconds() < 3600:  # Within last hour
                            self.last_alert_times[alert.alert_type] = alert_time
                    
                    # Rebuild active alerts
                    for alert in self.alerts_history:
                        if not alert.resolved:
                            self.active_alerts[alert.alert_type] = alert
                    
                    print(f"[ALERT] Loaded {len(self.alerts_history)} alerts from history")
            except Exception as e:
                print(f"[ALERT] Warning: Failed to load alert history: {e}")
    
    def _save_history(self):
        """Save alert history to disk."""
        try:
            data = {
                'alerts': [asdict(alert) for alert in self.alerts_history]
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ALERT] Warning: Failed to save alert history: {e}")
    
    def _should_send_alert(self, alert_type: str, severity: str) -> bool:
        """
        Check if alert should be sent based on throttling rules.
        
        Returns:
            True if alert should be sent, False if throttled
        """
        now = datetime.now(timezone.utc)
        
        # Check if we've sent this alert type recently
        if alert_type in self.last_alert_times:
            last_time = self.last_alert_times[alert_type]
            minutes_since = (now - last_time).total_seconds() / 60
            
            # Critical alerts can repeat after ALERT_REPEAT_INTERVAL_MINUTES
            if severity == "critical":
                if minutes_since < config.ALERT_REPEAT_INTERVAL_MINUTES:
                    print(f"[ALERT] Throttled {alert_type} (critical) - sent {minutes_since:.1f} min ago")
                    return False
            
            # Other alerts use MIN_ALERT_GAP_MINUTES
            else:
                if minutes_since < config.MIN_ALERT_GAP_MINUTES:
                    print(f"[ALERT] Throttled {alert_type} - sent {minutes_since:.1f} min ago")
                    return False
        
        return True
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"ALERT_{timestamp}_{len(self.alerts_history)}"
    
    def _format_phase_details(self, phase_stats: List) -> str:
        """Format phase statistics for alert message."""
        details = []
        for ps in phase_stats:
            details.append(
                f"  • Phase {ps.phase}: {ps.total_power_kw:.2f} kW "
                f"({ps.house_count} houses, {ps.avg_voltage:.1f}V avg)"
            )
        return "\n".join(details)
    
    def check_and_send_alerts(
        self,
        imbalance_kw: float,
        system_mode: str,
        phase_stats: List,
        phase_issues: Dict,
        power_issues: Dict
    ):
        """
        Check system status and send alerts if needed.
        
        Args:
            imbalance_kw: Current phase imbalance
            system_mode: "CONSUME" or "EXPORT"
            phase_stats: List of PhaseStats objects
            phase_issues: Dict of voltage issues
            power_issues: Dict of power issues
        """
        now = datetime.now(timezone.utc).isoformat()
        
        # Build phase details dict for storage
        phase_details = {
            'phases': [
                {
                    'phase': ps.phase,
                    'power_kw': ps.total_power_kw,
                    'voltage': ps.avg_voltage,
                    'house_count': ps.house_count
                }
                for ps in phase_stats
            ],
            'phase_issues': phase_issues,
            'power_issues': power_issues
        }
        
        phase_details_text = self._format_phase_details(phase_stats)
        
        # Check for critical imbalance
        if imbalance_kw >= config.ALERT_CRITICAL_IMBALANCE_KW:
            alert_type = "critical_imbalance"
            if self._should_send_alert(alert_type, "critical"):
                self._send_imbalance_alert(
                    alert_type=alert_type,
                    severity="critical",
                    imbalance_kw=imbalance_kw,
                    system_mode=system_mode,
                    phase_details=phase_details,
                    phase_details_text=phase_details_text,
                    timestamp=now
                )
        
        # Check for high imbalance (warning)
        elif imbalance_kw >= config.ALERT_HIGH_IMBALANCE_KW:
            alert_type = "high_imbalance"
            if self._should_send_alert(alert_type, "warning"):
                self._send_imbalance_alert(
                    alert_type=alert_type,
                    severity="warning",
                    imbalance_kw=imbalance_kw,
                    system_mode=system_mode,
                    phase_details=phase_details,
                    phase_details_text=phase_details_text,
                    timestamp=now
                )
        
        # Check if imbalance was resolved
        else:
            # If we had an active imbalance alert, mark it resolved
            for alert_type in ["critical_imbalance", "high_imbalance"]:
                if alert_type in self.active_alerts:
                    self._send_resolution_alert(
                        alert_type=alert_type,
                        imbalance_kw=imbalance_kw,
                        system_mode=system_mode,
                        phase_details=phase_details,
                        phase_details_text=phase_details_text,
                        timestamp=now
                    )
        
        # Check for voltage issues
        for issue_type, phases in phase_issues.items():
            if phases:
                self._check_voltage_issues(
                    issue_type=issue_type,
                    affected_phases=phases,
                    phase_stats=phase_stats,
                    timestamp=now
                )
    
    def _send_imbalance_alert(
        self,
        alert_type: str,
        severity: str,
        imbalance_kw: float,
        system_mode: str,
        phase_details: Dict,
        phase_details_text: str,
        timestamp: str
    ):
        """Send imbalance alert."""
        template = config.ALERT_TEMPLATES[alert_type]
        
        threshold = (config.ALERT_CRITICAL_IMBALANCE_KW 
                    if severity == "critical" 
                    else config.ALERT_HIGH_IMBALANCE_KW)
        
        subject = template["subject"].format(
            imbalance=imbalance_kw,
            threshold=threshold
        )
        
        message = template["body"].format(
            imbalance=imbalance_kw,
            threshold=threshold,
            mode=system_mode,
            timestamp=timestamp,
            phase_details=phase_details_text
        )
        
        # Send alert
        channels_result = self.alert_service.send_alert(
            subject=subject,
            message=message,
            severity=severity
        )
        
        # Create alert record
        alert = Alert(
            alert_id=self._generate_alert_id(),
            timestamp=timestamp,
            alert_type=alert_type,
            severity=severity,
            subject=subject,
            message=message,
            imbalance_kw=imbalance_kw,
            system_mode=system_mode,
            phase_details=phase_details,
            channels_sent=channels_result,
            resolved=False
        )
        
        # Update tracking
        self.alerts_history.append(alert)
        self.active_alerts[alert_type] = alert
        self.last_alert_times[alert_type] = datetime.now(timezone.utc)
        self._save_history()
        
        print(f"[ALERT] Sent {severity} alert: {subject}")
    
    def _send_resolution_alert(
        self,
        alert_type: str,
        imbalance_kw: float,
        system_mode: str,
        phase_details: Dict,
        phase_details_text: str,
        timestamp: str
    ):
        """Send alert resolution notification."""
        if alert_type not in self.active_alerts:
            return
        
        # Mark previous alert as resolved
        self.active_alerts[alert_type].resolved = True
        self.active_alerts[alert_type].resolved_at = timestamp
        del self.active_alerts[alert_type]
        
        # Send resolution notification (only if not recently sent)
        resolution_type = f"{alert_type}_resolved"
        if not self._should_send_alert(resolution_type, "info"):
            return
        
        template = config.ALERT_TEMPLATES["imbalance_resolved"]
        
        subject = template["subject"]
        message = template["body"].format(
            imbalance=imbalance_kw,
            mode=system_mode,
            timestamp=timestamp,
            phase_details=phase_details_text
        )
        
        channels_result = self.alert_service.send_alert(
            subject=subject,
            message=message,
            severity="info"
        )
        
        # Create resolution alert record
        alert = Alert(
            alert_id=self._generate_alert_id(),
            timestamp=timestamp,
            alert_type=resolution_type,
            severity="info",
            subject=subject,
            message=message,
            imbalance_kw=imbalance_kw,
            system_mode=system_mode,
            phase_details=phase_details,
            channels_sent=channels_result,
            resolved=True,
            resolved_at=timestamp
        )
        
        self.alerts_history.append(alert)
        self.last_alert_times[resolution_type] = datetime.now(timezone.utc)
        self._save_history()
        
        print(f"[ALERT] Sent resolution notification for {alert_type}")
    
    def _check_voltage_issues(
        self,
        issue_type: str,
        affected_phases: List,
        phase_stats: List,
        timestamp: str
    ):
        """Check and send voltage issue alerts."""
        for phase_name in affected_phases:
            alert_type = f"voltage_{issue_type.lower()}_{phase_name}"
            
            # Find phase stats
            ps = next((p for p in phase_stats if p.phase == phase_name), None)
            if not ps:
                continue
            
            # Determine severity
            severity = "warning"
            if issue_type == "OVER_VOLTAGE":
                threshold = config.OVERVOLTAGE_THRESHOLD
            else:  # UNDER_VOLTAGE
                threshold = config.UNDERVOLTAGE_THRESHOLD
            
            if not self._should_send_alert(alert_type, severity):
                continue
            
            template = config.ALERT_TEMPLATES["voltage_issue"]
            
            subject = template["subject"].format(phase=phase_name)
            message = template["body"].format(
                issue_type=issue_type.replace("_", " "),
                phase=phase_name,
                voltage=ps.avg_voltage,
                threshold=threshold,
                timestamp=timestamp
            )
            
            channels_result = self.alert_service.send_alert(
                subject=subject,
                message=message,
                severity=severity
            )
            
            alert = Alert(
                alert_id=self._generate_alert_id(),
                timestamp=timestamp,
                alert_type=alert_type,
                severity=severity,
                subject=subject,
                message=message,
                imbalance_kw=0.0,
                system_mode="N/A",
                phase_details={
                    'phase': phase_name,
                    'voltage': ps.avg_voltage,
                    'issue_type': issue_type
                },
                channels_sent=channels_result,
                resolved=False
            )
            
            self.alerts_history.append(alert)
            self.last_alert_times[alert_type] = datetime.now(timezone.utc)
            self._save_history()
            
            print(f"[ALERT] Sent voltage alert: {subject}")
    
    def get_alert_history(self, limit: int = 50, unresolved_only: bool = False) -> List[Dict]:
        """
        Get alert history.
        
        Args:
            limit: Maximum number of alerts to return
            unresolved_only: If True, only return unresolved alerts
        
        Returns:
            List of alert dictionaries
        """
        alerts = self.alerts_history
        
        if unresolved_only:
            alerts = [a for a in alerts if not a.resolved]
        
        # Return most recent first
        alerts = sorted(alerts, key=lambda a: a.timestamp, reverse=True)
        alerts = alerts[:limit]
        
        return [asdict(alert) for alert in alerts]
    
    def get_active_alerts(self) -> List[Dict]:
        """Get currently active (unresolved) alerts."""
        return [asdict(alert) for alert in self.active_alerts.values()]
    
    def test_alert_system(self) -> Dict:
        """Send test alerts through all configured channels."""
        subject = "🧪 Test Alert - Phase Balancing System"
        message = """
This is a test alert from the Phase Balancing Controller.

If you receive this message, the alert system is working correctly.

Test performed at: {timestamp}

Dashboard: http://localhost:8000
        """.format(timestamp=datetime.now().isoformat())
        
        results = self.alert_service.send_alert(
            subject=subject,
            message=message,
            severity="info"
        )
        
        return {
            "test_time": datetime.now().isoformat(),
            "channels_tested": results,
            "overall_status": "success" if any(results.values()) else "failed"
        }


# Global instance
_alert_manager = None

def get_alert_manager() -> AlertManager:
    """Get or create global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
