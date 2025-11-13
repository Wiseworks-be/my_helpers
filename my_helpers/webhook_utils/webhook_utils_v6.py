# WEBHOOK_UTILS_5
# ********************************************************************************************************************************************
# THIS SET OF HELPER FUNCTIONS IS ABOUT HTTPS CALLERS TO OTHER SYSTEMS
#
# Created by Marc De Krock
# 20250904: for reading a record, the row=None was not handled correctly, this is now fixed by     if rows == [None]: and not... if rows is None:
# 20251113: added retries + increased default timeout from 30 to 120 seconds
# ********************************************************************************************************************************************

import requests
import urllib.parse
import time
import json
from flask import jsonify
from my_helpers.exceptions.exceptions_v0 import (
    ExternalAPIError,
    MethodNotAllowedError,
    BadRequestError,
    BusinessRuleError,
)
from requests.exceptions import SSLError, RequestException


# *
def send_push_notification(message, api_key=None, device_id=None):
    url = f"https://www.pushsafer.com/api?k={api_key}&d={device_id}&m={message}"
    print("XXXXXXXXXXXXXX URL PUSH: ", url)
    response = requests.get(url)

    if response.status_code == 200:
        return "Notification sent successfully!"
    else:
        return f"Failed to send notification. Status code: {response.status_code}, Response: {response.text}"


# **********************************************************
def get_url(table, app_id=None, app_access_key=None):
    encoded_table = urllib.parse.quote(table)
    appsheet_url = f"https://api.appsheet.com/api/v2/apps/{app_id}/tables/{encoded_table}/Action?applicationAccessKey={app_access_key}"
    return appsheet_url


# **********************************************************
# Post data to AppSheet generic helper function
# changes made on 2025-08-22 by Marc De Krock
#   improved error handling
#   added parameter checks and informative error messages by a raising ExternalAPIError
# **********************************************************
def check_mandatory_args_1(args: dict):  # only when 'None' is not allowed
    """
    Checks that all mandatory function arguments are provided (not None).
    Empty lists/dicts are considered valid if explicitly passed.
    """
    missing = [k for k, v in args.items() if v is None]
    if missing:
        msg = f"Mandatory function argument(s) missing: {', '.join(missing)}"
        raise ExternalAPIError(msg)


def check_mandatory_args(
    args: dict,
):  # when both 'None' and empty string are not allowed
    missing = [k for k, v in args.items() if v in (None, "")]
    if missing:
        msg = f"Mandatory function argument(s) missing: {', '.join(missing)}"
        raise ExternalAPIError(msg)


def post_data_to_appsheet(
    table=None,
    rows=None,
    action=None,
    selector=None,
    app_name=None,
    app_id=None,
    app_access_key=None,
    user_settings=None,
    timeout_seconds=120,  # ⬅️ main fix
    max_retries=3,  # ⬅️ retry AppSheet slowness
):

    print("In post_data_to_appsheet")
    print("Table:", table)
    print("Rows:", rows)
    print("Action:", action)
    print("Selector:", selector)
    print("App Name:", app_name)
    print("App ID:", app_id)
    print("App Access Key:", app_access_key)
    print("User Settings:", user_settings)

    # ✓ Mandatory args
    mandatory_args = {
        "table": table,
        "rows": rows,
        "action": action,
        "app_name": app_name,
        "app_id": app_id,
        "app_access_key": app_access_key,
    }
    check_mandatory_args(mandatory_args)

    print("All mandatory arguments are provided ✅")

    # ✓ Fix rows=None edge case
    if rows == [None]:
        rows = []

    url_appsheet_app = get_url(table, app_id, app_access_key)
    print("URL:", url_appsheet_app)

    payload = {
        "Action": action,
        "Properties": {
            "Locale": "en-US",
            "Location": "51.159133, 4.806236",
            "Timezone": "Central European Standard Time",
        },
        "Rows": rows,
    }

    if selector:
        payload["Properties"]["Selector"] = selector
    if user_settings:
        payload["Properties"]["UserSettings"] = user_settings

    print("JSON FOR APPSHEET", json.dumps(payload, indent=2))

    # ─────────────────────────────────────────────
    #   RETRIES to avoid SSLEOFError & timeouts
    # ─────────────────────────────────────────────
    attempt = 1
    while attempt <= max_retries:
        try:
            print(f"📡 Calling AppSheet (attempt {attempt}/{max_retries})...")

            appsheet_response = requests.post(
                url_appsheet_app,
                json=payload,
                timeout=(15, timeout_seconds),
                # (connect timeout, read timeout)
            )

            # ✓ Success path
            if appsheet_response.status_code == 200:
                if not appsheet_response.text.strip():
                    raise ExternalAPIError(
                        f"No data returned from AppSheet, table={table}"
                    )
                print(f"Data posted to AppSheet table {table} successfully.")
                return appsheet_response

            # Non-200 → error
            raise ExternalAPIError(
                f"Failed posting to AppSheet table {table}. "
                f"Status={appsheet_response.status_code} | Response={appsheet_response.text}"
            )

        except SSLError as ssl_err:
            print(
                f"⚠️ SSL/Connection issue on attempt {attempt}/{max_retries}: {ssl_err}"
            )

        except RequestException as req_err:
            print(f"⚠️ Request error on attempt {attempt}/{max_retries}: {req_err}")

        # Retry with exponential backoff
        if attempt < max_retries:
            wait = 2 ** (attempt - 1)
            print(f"🔁 Retrying in {wait} s...")
            time.sleep(wait)

        attempt += 1

    # ───────────────────────────────
    # If we reach here → total failure
    # ───────────────────────────────
    raise ExternalAPIError(
        f"AppSheet unreachable after {max_retries} attempts for table {table}"
    )


# **********************************************************
