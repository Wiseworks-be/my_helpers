"""Notification utilities."""
import requests

def send_push_notification(message, api_key="AYIor8gFjJ5zb1k0Y7Pv", device_id="17595"):
    """Send push notification via Pushsafer."""
    url = f"https://www.pushsafer.com/api?k={api_key}&d={device_id}&m={message}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return "Notification sent successfully!"
    else:
        return f"Failed to send notification. Status code: {response.status_code}, Response: {response.text}"