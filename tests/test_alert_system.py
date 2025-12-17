"""
Test script for the alert system.

This script helps you verify that your alert configuration is working correctly.
"""
import sys
from alert_manager import get_alert_manager
import alert_config as config


def print_config_status():
    """Print current alert configuration."""
    print("\n" + "="*60)
    print("ALERT SYSTEM CONFIGURATION")
    print("="*60)
    
    print(f"\n📧 Email Alerts: {'✓ ENABLED' if config.EMAIL_ENABLED else '✗ DISABLED'}")
    if config.EMAIL_ENABLED:
        print(f"   SMTP Server: {config.EMAIL_SMTP_HOST}:{config.EMAIL_SMTP_PORT}")
        print(f"   From: {config.EMAIL_SMTP_USER}")
        print(f"   To: {config.ENGINEER_EMAIL}")
        if config.ALERT_CC_EMAILS:
            print(f"   CC: {', '.join(config.ALERT_CC_EMAILS)}")
    
    print(f"\n📱 SMS Alerts: {'✓ ENABLED' if config.SMS_ENABLED else '✗ DISABLED'}")
    if config.SMS_ENABLED:
        print(f"   From: {config.TWILIO_FROM_NUMBER}")
        print(f"   To: {config.ENGINEER_PHONE}")
    
    print(f"\n🔗 Webhook Alerts: {'✓ ENABLED' if config.WEBHOOK_ENABLED else '✗ DISABLED'}")
    if config.WEBHOOK_ENABLED:
        print(f"   Type: {config.WEBHOOK_TYPE}")
        print(f"   URL: {config.WEBHOOK_URL[:50]}...")
    
    print(f"\n⚙️  Alert Thresholds:")
    print(f"   High Imbalance: {config.ALERT_HIGH_IMBALANCE_KW} kW")
    print(f"   Critical Imbalance: {config.ALERT_CRITICAL_IMBALANCE_KW} kW")
    print(f"   Min Alert Gap: {config.MIN_ALERT_GAP_MINUTES} minutes")
    print(f"   Repeat Interval: {config.ALERT_REPEAT_INTERVAL_MINUTES} minutes")


def test_alerts():
    """Send test alerts through all configured channels."""
    print("\n" + "="*60)
    print("TESTING ALERT SYSTEM")
    print("="*60)
    
    print("\nSending test alerts through all configured channels...")
    print("(Check your email, phone, and chat app)")
    
    alert_manager = get_alert_manager()
    result = alert_manager.test_alert_system()
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    channels = result.get('channels_tested', {})
    
    for channel, success in channels.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"   {channel.upper()}: {status}")
    
    overall = result.get('overall_status', 'unknown')
    if overall == 'success':
        print("\n✓ Alert system is working!")
    else:
        print("\n✗ Alert system test failed. Check configuration.")
    
    print("\nTest completed at:", result.get('test_time'))


def show_alert_history():
    """Display recent alert history."""
    print("\n" + "="*60)
    print("RECENT ALERT HISTORY")
    print("="*60)
    
    alert_manager = get_alert_manager()
    alerts = alert_manager.get_alert_history(limit=10)
    
    if not alerts:
        print("\nNo alerts in history.")
        return
    
    for alert in alerts:
        timestamp = alert.get('timestamp', 'Unknown')
        alert_type = alert.get('alert_type', 'Unknown')
        severity = alert.get('severity', 'info').upper()
        subject = alert.get('subject', 'No subject')
        resolved = alert.get('resolved', False)
        
        print(f"\n[{timestamp}] {severity}")
        print(f"   Type: {alert_type}")
        print(f"   Subject: {subject}")
        print(f"   Status: {'✓ RESOLVED' if resolved else '⚠ ACTIVE'}")


def show_active_alerts():
    """Display currently active (unresolved) alerts."""
    print("\n" + "="*60)
    print("ACTIVE ALERTS")
    print("="*60)
    
    alert_manager = get_alert_manager()
    alerts = alert_manager.get_active_alerts()
    
    if not alerts:
        print("\n✓ No active alerts. System is healthy!")
        return
    
    print(f"\n⚠ {len(alerts)} active alert(s) require attention:\n")
    
    for alert in alerts:
        timestamp = alert.get('timestamp', 'Unknown')
        alert_type = alert.get('alert_type', 'Unknown')
        severity = alert.get('severity', 'info').upper()
        subject = alert.get('subject', 'No subject')
        imbalance = alert.get('imbalance_kw', 0)
        
        print(f"[{severity}] {subject}")
        print(f"   Time: {timestamp}")
        print(f"   Type: {alert_type}")
        print(f"   Imbalance: {imbalance:.2f} kW")
        print()


def print_menu():
    """Print the main menu."""
    print("\n" + "="*60)
    print("ALERT SYSTEM TEST UTILITY")
    print("="*60)
    print("\n1. Show configuration")
    print("2. Send test alerts")
    print("3. Show alert history")
    print("4. Show active alerts")
    print("5. Exit")
    print()


def main():
    """Main menu loop."""
    while True:
        print_menu()
        
        try:
            choice = input("Select an option (1-5): ").strip()
            
            if choice == '1':
                print_config_status()
            elif choice == '2':
                test_alerts()
            elif choice == '3':
                show_alert_history()
            elif choice == '4':
                show_active_alerts()
            elif choice == '5':
                print("\nExiting...")
                break
            else:
                print("\n✗ Invalid option. Please select 1-5.")
            
            input("\nPress Enter to continue...")
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
