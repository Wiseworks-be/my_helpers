"""AppSheet integration utilities."""
import requests
import urllib.parse
import json

def get_appsheet_url(table, app_id, app_access_key):
    """Generate AppSheet API URL for a table."""
    encoded_table = urllib.parse.quote(table)
    return f"https://api.appsheet.com/api/v2/apps/{app_id}/tables/{encoded_table}/Action?applicationAccessKey={app_access_key}"

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
    """Post data to AppSheet with comprehensive error handling."""
    from .errors import check_mandatory_args
    
    # Check mandatory parameters
    mandatory_args = {
        "table": table,
        "rows": rows,
        "action": action,
        "app_name": app_name,
        "app_id": app_id,
        "app_access_key": app_access_key,
    }
    check_mandatory_args(mandatory_args)
    
    if rows is None:
        rows = []
    
    url = get_appsheet_url(table, app_id, app_access_key)
    
    payload = {
        "Action": action,
        "Properties": {
            "Locale": "en-US",
            "Location": "51.159133, 4.806236",
            "Timezone": "Central European Standard Time",
        },
        "Rows": rows,
    }
    
    # Optional parameters
    if selector:
        payload["Properties"]["Selector"] = selector
    if user_settings:
        payload["Properties"]["UserSettings"] = user_settings
    
    # Make the request
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        if not response.text or response.text.strip() == "":
            raise ValueError(f"No data returned from AppSheet, so NO DATA POSTED to table {table}.")
        return response
    else:
        raise ValueError(f"Failed to post data to AppSheet table {table}. Status code: {response.status_code}, Response: {response.text}")