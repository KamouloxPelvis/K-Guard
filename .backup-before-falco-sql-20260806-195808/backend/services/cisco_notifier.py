import requests
import backend.database

class CiscoWebexNotifier:
    def __init__(self):
        """
        Initializes the Webex Notifier. 
        Configuration is fetched dynamically from the database to support runtime updates.
        """
        self.api_url = "https://webexapis.com/v1/messages"

    def _get_config(self):
        """
        Helper to fetch the latest integration settings from the SQLite database.
        Returns (token, room_id, enabled).
        """
        settings = backend.database.get_integration_settings("webex")
        if not settings:
            return None, None, False
        
        return settings.get('token'), settings.get('target_id'), bool(settings.get('enabled'))

    def send_scan_report(self, image, summary):
        """
        Sends a formatted security scan report to the configured Cisco Webex room.
        Fetches current credentials before each transmission to ensure synchronization.
        """
        token, room_id, enabled = self._get_config()
        
        # Validation: Stop if integration is disabled or credentials missing
        if not enabled or not token or not room_id:
            return
        
        # Select status emoji based on vulnerability severity
        status_emoji = "🚨" if summary['critical'] > 0 else "✅"
        
        # Constructing the Markdown message for Webex
        msg = (
            f"{status_emoji} **K-Guard Security Scan Report**\n\n"
            f"**Target Image:** `{image}`\n"
            f"**Critical Vulnerabilities:** {summary['critical']}\n"
            f"**High Vulnerabilities:** {summary['high']}\n"
            f"**Security Status:** {'🔴 Action Required' if summary['critical'] > 0 else '🟢 Compliant'}"
        )
        
        try:
            # Perform the POST request to Cisco Webex API
            # Authorization is pulled from the database in real-time
            requests.post(
                self.api_url, 
                json={"roomId": room_id, "markdown": msg},
                headers={"Authorization": f"Bearer {token}"}, 
                timeout=5
            )
        except Exception as e:
            # Failure to notify shouldn't crash the main scanning process
            print(f"❌ Webex Notification Error: {e}")