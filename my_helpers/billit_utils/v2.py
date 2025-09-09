from flask import jsonify
import requests
import json
import logging
import os
# from dotenv import load_dotenv
from my_helpers.exceptions import ExternalAPIError
# Function to post an order to Billit
# This function takes a payload, which is a JSON object,
# and sends it to the Billit API to create an order.
# It returns the response from Billit.
# please note that this only posts the order to Billit, next the order needs to be sent
def post_order_to_billit(payload, BILLIT_API_KEY, BILLIT_ORDERS_URL):
    # This function would contain the logic to send the payload to Billit.
    # For now, we will just print the payload.
    print("Sending order to Billit:", json.dumps(payload, indent=2))
    url = BILLIT_ORDERS_URL  # Replace with the actual Billit API endpoint
    headers = {
        "Content-Type": "text/json",
        "Accept": "*/*",
        "apiKey": BILLIT_API_KEY,
        "User-Agent": "PostmanRuntime/7.44.1",
        "Accept-Encoding": "gzip, deflate, br",
    }  # Replace with your actual API key

    response = requests.post(url, headers=headers, json=payload)
    response_status = response.status_code
    if response.status_code == 200:
        print("Order posted successfully:", response.json())
    else:
        print("Failed to post order to Billit:", response_status)
        raise ExternalAPIError(
            f"Failed to send order to Billit: {response.status_code}, Response: {response.text}"
        )
    return int(response.json())
