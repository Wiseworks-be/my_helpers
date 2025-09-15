# WEBHOOK_UTILS_4
# ********************************************************************************************************************************************
# THIS SET OF HELPER FUNCTIONS IS ABOUT HTTPS CALLERS TO OTHER SYSTEMS
#
# Created by Marc De Krock
# 20250904: for reading a record, the row=None was not handled correctly, this is now fixed by     if rows == [None]: and not... if rows is None:
# ********************************************************************************************************************************************

import requests
import urllib.parse
import json
from flask import jsonify
from my_helpers.exceptions.exceptions_v0 import (
    ExternalAPIError,
    MethodNotAllowedError,
    BadRequestError,
    BusinessRuleError,
)


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
def check_mandatory_args(args: dict):
    """
    Checks that all mandatory function arguments are provided (not None or empty).
    Raises ExternalAPIError listing which arguments are missing.
    """
    missing = [k for k, v in args.items() if not v]
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
    # CHECK MANDATORY PARAMETERS
    # define which ones are mandatory
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

    # ALL MANDATORY PARAMETERS ARE PRESENT
    print("OK, lets do the call to AppSheet")
    print("App Name:", app_name)
    print("rows=", rows)
    if rows == [None]:
        print("ROWS is NONE")
        rows = []  # make sure it's an empty list, not [None]
    url_appsheet_app = get_url(table, app_id, app_access_key)
    print("URL:", url_appsheet_app)
    # table to address
    # Headers
    # none
    # JSON payload
    # `Add`: Adds a new row to the table.
    # `Delete`: Deletes existing rows from the table.
    # `Edit`: Updates existing rows in the table.
    # `Find`: Reads an existing row of the table.

    payload = {
        "Action": action,
        "Properties": {
            "Locale": "en-US",
            "Location": "51.159133, 4.806236",
            "Timezone": "Central European Standard Time",
        },
        "Rows": rows,
    }
    # optional parameters:
    if selector:
        payload["Properties"]["Selector"] = selector
    if user_settings:
        payload["Properties"]["UserSettings"] = user_settings
    # FINAL JSON PAYLOAD
    print("JSON FOR APPSHEET", json.dumps(payload, indent=2))
    # POST to APPSHEET
    appsheet_response = requests.post(url_appsheet_app, json=payload)
    # check now response
    # response code 200 is OK, but we also need to check if data was returned
    # if no data returned, this means no record created or updated ini AppSheet
    # so we raise an error in that case too
    # else we return the full response object
    # for further processing by the calling function if needed
    table_name = table
    if appsheet_response.status_code == 200:
        if not appsheet_response.text or appsheet_response.text.strip() == "":
            # no data returned, this means no record created or updated
            print(
                f"No data returned from AppSheet, so NO DATA POSTED to table {table_name}."
            )
            raise ExternalAPIError(
                f"No data returned from AppSheet, so NO DATA POSTED to table {table_name}."
            )
        else:
            print(f"Data posted to AppSheet table {table_name} successfully.")
            return appsheet_response
    else:
        print(
            f"Failed to post data to AppSheet table {table_name}. Status code: {appsheet_response.status_code}, Response: {appsheet_response.text}"
        )
        raise ExternalAPIError(
            f"Failed to post data to AppSheet table {table_name}. Status code: {appsheet_response.status_code}, Response: {appsheet_response.text}"
        )


# **********************************************************
