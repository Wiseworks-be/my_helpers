import requests
import urllib.parse
import json
from flask import jsonify
from my_helpers.exceptions import (
    ExternalAPIError,
    MethodNotAllowedError,
    BadRequestError,
    BusinessRuleError,
)
def send_push_notification(message):
    url = f"https://www.pushsafer.com/api?k=AYIor8gFjJ5zb1k0Y7Pv&d=17595&m={message}"
    response = requests.get(url)

    if response.status_code == 200:
        return "Notification sent successfully!"
    else:
        return f"Failed to send notification. Status code: {response.status_code}, Response: {response.text}"
