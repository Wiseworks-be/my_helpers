"""Billit integration utilities."""

def format_invoice_data(invoice_items):
    """Format invoice data for Billit."""
    total = 0
    formatted_items = []
    
    for item in invoice_items:
        item_total = item.get("quantity", 1) * item.get("unit_price", 0)
        formatted_items.append({
            "description": item.get("description", ""),
            "quantity": item.get("quantity", 1),
            "unit_price": item.get("unit_price", 0),
            "total": item_total
        })
        total += item_total
    
    return {
        "items": formatted_items,
        "total_amount": total,
        "currency": "EUR"
    }

# billit_utils_1.py
# Improved version with better error handling and logging
# created by Marc De Krock
# date: 2025-08-22

from flask import jsonify
import requests
import json
import logging
import os
from dotenv import load_dotenv
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


def send_order(order_id, transport_type, BILLIT_API_KEY, BILLIT_SEND_INVOICE_URL):
    """
    Sends an order to Billit using the provided order ID and method of transport.

    :param order_id: str - The ID of the order to send
    :param method_of_transport: str - The method of transport for the order
    :return: dict - The payload containing the order details
    :return: Response from the Billit API
    """
    print(f"Sending order {order_id} with transport type {transport_type} to Billit")
    if transport_type not in [
        "SMTP",
        "Letter",
        "Peppol",
        "SDI",
        "KSeF",
        "OSA",
        "ANAF",
        "SAT",
    ]:
        print(f"error: Invalid transport type: {transport_type}")
        raise ValueError(f"error: Invalid transport type: {transport_type}", 403)

    url = BILLIT_SEND_INVOICE_URL
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "apiKey": BILLIT_API_KEY,
    }

    payload = {
        "Transporttype": transport_type,
        "OrderIDs": [order_id],
    }
    print("Payload for sending order:", json.dumps(payload, indent=2))
    response = requests.post(url, headers=headers, json=payload)
    response_status = response.status_code
    print("Response status code:", response_status)

    if response_status == 200:
        print("Order sent successfully:", response_status)
        return response_status
    else:
        print("Failed to transport order to Billit:", response_status)
        raise ExternalAPIError(
            f"Failed to transport order to Billit: {response.status_code}, Response: {response.text}"
        )


def get_billit_order(order_id, BILLIT_API_KEY, BILLIT_ORDERS_URL):
    """
    Fetches an order from the Billit API based on order_id.

    Args:
        order_id (str): The unique identifier of the order.
        base_url (str): Base URL of the Billit API (e.g., https://api.billit.be).
        api_key (str): Your Billit API token.

    Returns:
        dict: The JSON response containing order details, or None if not found or error.
    """
    url = f"{BILLIT_ORDERS_URL}/{order_id}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "apiKey": BILLIT_API_KEY,
        "User-Agent": "PostmanRuntime/7.44.1",
        "Accept-Encoding": "gzip, deflate, br",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print(
            f"Order id fetched successfuly: {order_id}. Status: {response.status_code}"
        )
        return response.json(), response.status_code
    else:
        print(f"Failed to fetch order {order_id}. Status: {response.status_code}")
        print("Response:", response.text)
        raise ExternalAPIError(
            f"Failed to fetch order {order_id}. Status: {response.status_code}, Response: {response.text}"
        )


def fetch_billit_file(file_id, BILLIT_API_KEY, BILLIT_FILES_URL):
    url = f"{BILLIT_FILES_URL}/{file_id}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "apiKey": BILLIT_API_KEY,
        "User-Agent": "PostmanRuntime/7.44.1",
        "Accept-Encoding": "gzip, deflate, br",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print(
            f"File content fetched successfuly: {file_id}. Status: {response.status_code}"
        )
        return response.json(), response.status_code
    else:
        print(
            f"Failed to fetch file content for file id: {file_id}. Status: {response.status_code}"
        )
        print("Response:", response.text)
        raise ExternalAPIError(
            f"Failed to fetch file content for file id: {file_id}. Status: {response.status_code}, Response: {response.text}"
        )


# --- Helper functions for Billit API ---
def _billit_api_call(
    method, endpoint, BILLIT_API_KEY, BILLIT_BASE_URL, params=None, data=None
):
    """
    Helper to make authenticated calls to the Billit API.
    """
    if not BILLIT_BASE_URL or not BILLIT_API_KEY:
        raise ValueError("Billit API base URL or API Key not configured.")

    url = f"{BILLIT_BASE_URL}{endpoint}"
    headers = {"ApiKey": BILLIT_API_KEY, "Accept": "application/json"}
    if data:  # For POST/PUT if Billit ever requires them
        headers["Content-Type"] = "application/json"

    try:
        response = requests.request(
            method, url, headers=headers, params=params, json=data
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Billit API call failed: {method} {url} - {e}")
        if hasattr(e, "response") and e.response is not None:
            logging.error(f"Billit API Error Response: {e.response.text}")
        raise


def get_billit_order_details(order_id, BILLIT_API_KEY, BILLIT_BASE_URL):
    """Fetches full order details from Billit API."""
    logging.info(f"Fetching order details for ID: {order_id}")
    return _billit_api_call(
        "GET", f"/v1/orders/{order_id}", BILLIT_API_KEY, BILLIT_BASE_URL
    )


def get_billit_file_content(file_id, BILLIT_API_KEY, BILLIT_BASE_URL):
    """Fetches file content (base64) from Billit API."""
    logging.info(f"Fetching file content for FileID: {file_id}")
    return _billit_api_call(
        "GET", f"/v1/files/{file_id}", BILLIT_API_KEY, BILLIT_BASE_URL
    )
