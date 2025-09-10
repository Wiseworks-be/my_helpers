# 20250909, Marc De Krock
# cleaning updated to support \u20ac removal
# cleaning update to support 17-05-2023 => 2025-05-17
import re
from datetime import datetime
import json


# *****************************************************
def capitalize_keys(data):
    if isinstance(data, dict):
        return {
            key[0].upper() + key[1:] if key else key: capitalize_keys(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [capitalize_keys(item) for item in data]
    else:
        return data


# *****************************************************
def replace_empty_values(data):
    if isinstance(data, dict):
        return {
            key: (
                replace_empty_values(value)
                if isinstance(value, (dict, list))
                else ("-" if value in ("", None) else value)
            )
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [replace_empty_values(item) for item in data]
    else:
        return "-" if data in ("", None) else data


# *****************************************************
def clean_money_in_json(data):
    if isinstance(data, dict):
        return {k: clean_money_in_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_money_in_json(item) for item in data]
    elif isinstance(data, str):
        # Match and clean Euro-formatted money strings like "€1,752.66"
        # match = re.match(r"^€?\s*[\d,]+\.\d{2}$", data.strip())
        match = re.match(
            r"^€?\s*[\d,]+\.\d{1,2}$", data.strip()
        )  # Allow 1 or 2 decimal places
        if match:
            clean = data.replace("€", "").replace(",", "").strip()
            return clean
        return data
    else:
        return data


def clean_money_in_json_2(data):
    if isinstance(data, dict):
        return {k: clean_money_in_json_2(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_money_in_json_2(item) for item in data]
    elif isinstance(data, str):
        s = data.strip()
        # Always strip euro symbol and spaces
        s = s.replace("€", "").replace("\u20ac", "").replace(" ", "")
        # If it contains digits, assume it's numeric
        if any(ch.isdigit() for ch in s):
            # Convert European format -> dot decimals
            if "," in s:
                s = s.replace(".", "").replace(",", ".")
            try:
                return float(s)
            except ValueError:
                return s
        return data
    else:
        return data


# *****************************************************
def extract_vat_percentage(vat_string):
    return int(float(vat_string.strip().replace("%", "")))


# *****************************************************
def clean_vat_in_json(data):
    if isinstance(data, dict):
        return {k: clean_vat_in_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_vat_in_json(item) for item in data]
    elif isinstance(data, str):
        match = re.match(r"^\d+(\.\d+)?%$", data.strip())
        if match:
            return int(float(data.strip().replace("%", "")))
        return data
    else:
        return data


# *****************************************************
def split_supplier_address_for_template(address):
    parts = [part.strip() for part in address.split(",")]

    if len(parts) == 3:
        street_and_nr, postal_city, country = parts
    elif len(parts) == 2:
        street_and_nr, postal_city = parts
        country = ""  # fallback if country is missing
    else:
        raise ValueError("Unexpected address format")

    postal_parts = postal_city.strip().split(" ", 1)
    postalcode = postal_parts[0]
    city = postal_parts[1] if len(postal_parts) > 1 else ""

    return {
        "P_supplier_address_streetname": street_and_nr,
        "P_supplier_address_postalzone": postalcode,
        "P_supplier_address_city": city,
        "P_supplier_address_country": country,
    }


# *****************************************************
def split_customer_address_for_template(address):
    parts = [part.strip() for part in address.split(",")]

    if len(parts) == 3:
        street_and_nr, postal_city, country = parts
    elif len(parts) == 2:
        street_and_nr, postal_city = parts
        country = ""  # fallback if country is missing
    else:
        raise ValueError("Unexpected address format")

    postal_parts = postal_city.strip().split(" ", 1)
    postalcode = postal_parts[0]
    city = postal_parts[1] if len(postal_parts) > 1 else ""
    return {
        "P_customer_address_streetname": street_and_nr,
        "P_customer_address_postalzone": postalcode,
        "P_customer_address_city": city,
        "P_customer_address_country": country,
    }


# *****************************************************
def normalize_keys(data):
    if isinstance(data, dict):
        return {
            key.replace(" ", "_"): normalize_keys(value) for key, value in data.items()
        }
    elif isinstance(data, list):
        return [normalize_keys(item) for item in data]
    else:
        return data


# *****************************************************
# ** FUNCTION to make the dates in the JSON normalized **
def reformat_dates_in_json(data, input_format="%m/%d/%Y", output_format="%d/%m/%Y"):
    """
    Recursively reformats date strings in a nested JSON-like structure.

    :param data: The JSON-like structure (dict/list)
    :param input_format: The expected format of the input date strings
    :param output_format: The desired format of the output date strings
    :return: A new structure with reformatted date strings
    """
    if isinstance(data, dict):
        return {
            key: reformat_dates_in_json(value, input_format, output_format)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [
            reformat_dates_in_json(item, input_format, output_format) for item in data
        ]
    elif isinstance(data, str):
        try:
            dt = datetime.strptime(data, input_format)
            return dt.strftime(output_format)
        except ValueError:
            return data  # Not a date string, return as-is
    else:
        return data  # Return all non-string values unchanged


# *****************************************************
def convert_numeric_strings(data):
    if isinstance(data, dict):
        return {k: convert_numeric_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_numeric_strings(item) for item in data]
    elif isinstance(data, str):
        s = data.strip().replace(",", "")

        # Try float first (to support decimals), then int if applicable
        if re.fullmatch(r"\d+\.\d+", s):
            return float(s)
        elif s.isdigit():
            return int(s)
        else:
            return data
    else:
        return data


# *****************************************************
def clean_json_data(data):
    """
    Cleans the JSON data by capitalizing keys, replacing empty values, and normalizing keys and reformatting the dates to Peppol requirements.

    :param data: The JSON data to clean
    :return: The cleaned JSON data
    """
    data = capitalize_keys(data)
    # print("data after capitalize_keys",data)
    # data = replace_empty_values(data)
    # print("data after replace_empty_values",data)
    print("clean_money_in_json_2 BEFORE", json.dumps(data, indent=2))
    data = clean_money_in_json_2(data)
    print("clean_money_in_json_2 AFTER", json.dumps(data, indent=2))
    # print("data after clean_money_in_json",data)
    data = clean_vat_in_json(data)
    # print("data after clean_vat_in_json",data)
    # data = split_supplier_address_for_template(data.get("supplier_address", ""))
    # print("data after split_supplier_address_for_template",data)
    data = normalize_keys(data)
    # print("data after normalize_keys",data)
    print("reformat date BEFORE", json.dumps(data, indent=2))
    data = reformat_dates_in_json(
        data, "%m/%d/%Y", "%Y-%m-%d"
    )  # if this does not work, 05/17/2023 => 2023-05-17
    data = reformat_dates_in_json(
        data, "%d-%m-%Y", "%Y-%m-%d"
    )  # do this: 17-05-2023 => 2023-05-17
    print("reformat date AFTER", json.dumps(data, indent=2))
    # print("data after reformat_dates_in_json",data)
    # data = convert_string_numbers_in_json(data)
    data = convert_numeric_strings(data)
    return data


# *****************************************************
def format_number_eu(value):
    """Convert float to EU formatted string: 11560.00 → '11.560,00'"""
    s = f"{value:,.2f}"  # '11,560.00'
    s = s.replace(",", "X").replace(".", ",").replace("X", " ")
    return s


def try_convert_string_number(value):
    # Try to parse as float
    num = float(value)
    return format_number_eu(num)


def convert_string_numbers_in_json(data):
    """Recursively convert numeric strings in JSON-like structure to EU format."""
    if isinstance(data, dict):
        return {k: convert_string_numbers_in_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_string_numbers_in_json(item) for item in data]
    elif isinstance(data, str):
        return try_convert_string_number(value=data)
    else:
        return data  # Leave other types untouched (e.g., bool, None)


# *****************************************************
# Function to merge three nested objects into a single JSON object
# This function takes a JSON body and three nested objects (customer, supplier, order_lines),
# and merges them into a single JSON object.
def merge_objects(json_body, customer, supplier, order_lines):
    # Start with a copy of object 1, but remove any existing conflicting keys
    result = {
        key: value
        for key, value in json_body.items()
        if key not in ("customer", "supplier", "order_lines")
    }

    # Add/override with the three nested objects
    result["Customer"] = customer
    result["Supplier"] = supplier
    result["OrderLines"] = order_lines

    return result


# Function to map JSON keys based on provided rules
# This function takes an input JSON and a set of mapping rules,
# and returns a new JSON with keys transformed according to the rules.
def map_json(input_data, mapping_rules):
    """
    Maps input JSON keys to a new JSON format based on mapping rules.

    :param input_data: dict - incoming JSON
    :param mapping_rules: dict - defines how input keys map to output keys
                               - values can be strings (direct mapping)
                               - or (output_key, transform_fn) tuples
    :return: dict - transformed output JSON
    """
    output_data = {}
    for input_key, rule in mapping_rules.items():
        if input_key in input_data:
            value = input_data[input_key]
            if isinstance(rule, tuple):
                output_key, transform_fn = rule
                output_data[output_key] = transform_fn(value)
            else:
                output_data[rule] = value
        else:
            print(f"Warning: input key '{input_key}' not found in input data.")
    return output_data


# Function to split supplier address into components
# This function takes a supplier address string and splits it into street, postal code, city,
# and country components. It returns a dictionary with these components.
# If the address format is unexpected, it returns empty strings and an error message.
def split_supplier_address_for_template(address):
    parts = [part.strip() for part in address.split(",")]

    if len(parts) == 3:
        street_and_nr, postal_city, country = parts
    elif len(parts) == 2:
        street_and_nr, postal_city = parts
        country = ""  # fallback if country is missing
    else:
        raise ValueError("Unexpected address format")

    postal_parts = postal_city.strip().split(" ", 1)
    postalcode = postal_parts[0]
    city = postal_parts[1] if len(postal_parts) > 1 else ""

    return {
        "P_supplier_address_streetname": street_and_nr,
        "P_supplier_address_postalzone": postalcode,
        "P_supplier_address_city": city,
        "P_supplier_address_country": country,
    }


def split_address_advanced(address, address_type):
    # Split into parts by commas and clean
    parts = [part.strip() for part in address.split(",")]

    # Initialize fields
    street = nr = box = postalcode = city = country = ""

    # Handle country and postal/city
    if len(parts) >= 3:
        country = parts[-1]
        postal_city_part = parts[-2]
        remaining_parts = parts[:-2]
    elif len(parts) == 2:
        postal_city_part = parts[-1]
        remaining_parts = parts[:-1]
    else:
        raise ValueError("Unexpected address format")

    # Parse postalcode and city
    postal_parts = postal_city_part.strip().split(" ", 1)
    postalcode = postal_parts[0]
    city = postal_parts[1] if len(postal_parts) > 1 else ""

    # Look for box in remaining_parts
    box_candidate = None
    street_candidate = []
    for part in remaining_parts:
        if re.match(r"(?i)^box\s*\d+$", part):
            box_candidate = part
        else:
            street_candidate.append(part)

    if box_candidate:
        box_match = re.match(r"(?i)^box\s*(\d+)$", box_candidate)
        if box_match:
            box = box_match.group(1)

    # Join street parts and extract street and number
    street_full = " ".join(street_candidate)
    street_match = re.match(
        r"""^(.*?)              # Street name
            [\s,]+              # Space or comma
            (\d+)               # House number
            (?:\s*[-]\s*(\d+))? # Optional: hyphen followed by box number
        $""",
        street_full,
        re.IGNORECASE | re.VERBOSE,
    )

    if street_match:
        street = street_match.group(1).strip()
        nr = street_match.group(2)
        if not box and street_match.group(3):  # hyphen box as fallback
            box = street_match.group(3)
    if address_type == "supplier":
        return {
            "P_supplier_address_streetname": street,
            "P_supplier_address_streetnumber": nr,
            "P_supplier_address_box": box,
            "P_supplier_address_postalzone": postalcode,
            "P_supplier_address_city": city,
            "P_supplier_address_country": country,
        }
    elif address_type == "customer":
        return {
            "P_customer_address_streetname": street,
            "P_customer_address_streetnumber": nr,
            "P_customer_address_box": box,
            "P_customer_address_postalzone": postalcode,
            "P_customer_address_city": city,
            "P_customer_address_country": country,
        }
    else:
        raise ValueError(
            "Invalid address type specified. Use 'supplier' or 'customer'."
        )