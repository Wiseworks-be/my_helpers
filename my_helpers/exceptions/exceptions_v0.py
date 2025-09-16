# define here exceptions for the application
import logging
import requests
from json.decoder import JSONDecodeError


class ExternalAPIError(Exception):
    """Raised when an external API call (Billit, AppSheet, etc.) fails."""

    pass


class BusinessRuleError(Exception):
    """Raised when a business rule is violated (e.g. duplicate invoice)."""

    pass


class MethodNotAllowedError(Exception):
    """Raised when an unsupported HTTP method is used."""

    pass


class BadRequestError(Exception):
    """Raised when the request body or parameters are invalid."""

    pass


class BillitOrderNotFound(Exception):
    pass


class BillitOrderPDFTimeout(Exception):
    pass


# generic exception handler for Functions Framework
# maps exceptions to (message, HTTP status code)
# This is used to handle exceptions in a consistent way across the application.
def handle_exception(e):
    """
    Maps exceptions to (message, HTTP status code).
    """
    # --- Input / client errors ---
    if isinstance(e, ValueError):
        logging.error(f"ValueError: {e}")
        return (f"Bad Request: {e}", 400)

    if isinstance(e, KeyError):
        logging.error(f"Missing key: {e}")
        return (f"Bad Request - Missing key: {e}", 400)

    if isinstance(e, JSONDecodeError):
        logging.error(f"Invalid JSON: {e}")
        return (f"Malformed JSON input: {e}", 400)

    # --- Requests / external API errors ---
    if isinstance(e, requests.exceptions.Timeout):
        logging.error(f"Request timed out: {e}")
        return (f"External service timeout: {e}", 504)

    if isinstance(e, requests.exceptions.ConnectionError):
        logging.error(f"Connection error: {e}")
        return (f"External service unavailable: {e}", 502)

    if isinstance(e, requests.exceptions.HTTPError):
        logging.error(f"External API returned bad status: {e}")
        return (f"Error from external API: {e}", 502)

    if isinstance(e, requests.exceptions.SSLError):
        logging.error(f"SSL verification failed: {e}")
        return (f"SSL verification error: {e}", 502)

    if isinstance(e, requests.exceptions.RequestException):
        logging.error(f"General requests exception: {e}")
        return (f"Error communicating with external service: {e}", 502)

    # --- System / file related ---
    if isinstance(e, FileNotFoundError):
        logging.error(f"File not found: {e}")
        return (f"File not found: {e}", 404)

    if isinstance(e, PermissionError):
        logging.error(f"Permission denied: {e}")
        return (f"Permission denied: {e}", 403)

    if isinstance(e, TimeoutError):
        logging.error(f"System timeout: {e}")
        return (f"Internal operation timed out: {e}", 504)

    # --- Custom app-level errors ---
    if isinstance(e, ExternalAPIError):
        logging.error(f"AppSheet/External API error: {e}")
        return (f"{e}", 502)  # propagate the exact message you raised

    if isinstance(e, MethodNotAllowedError):
        logging.error(f"Method not allowed: {e}")
        return ("Method Not Allowed", 405)
    if isinstance(e, BadRequestError):
        logging.error(f"Bad request: {e}")
        return (f"Bad Request: {e}", 400)

    # --- Catch-all for unexpected errors ---
    logging.error(f"Unexpected error: {e}", exc_info=True)
    return (f"Unexpected error: {e}", 500)
