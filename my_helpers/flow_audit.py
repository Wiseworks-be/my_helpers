# audit_helpers.py
import logging
import traceback
from flask import jsonify

def log_step(run_id, step_name, status, logs):
    """
    Simple placeholder for your audit logging.
    Replace with your actual Firestore/BigQuery logging later.
    """
    logging.info(f"[{run_id}] {step_name} - {status} - {logs}")

def flow_with_audit_logging(handler_func, flow_name, request, no_error="YES"):
    """
    Wraps your handler function with basic error handling and logging.
    """
    run_id = f"{flow_name}-{id(request)}"
    try:
        return handler_func(request, run_id=run_id)
    except Exception as e:
        logging.error(f"[{run_id}] {flow_name} failed: {e}\n{traceback.format_exc()}")
        if no_error == "YES":
            # Always return 200 for AppSheet retry protection
            return jsonify({"status": "error", "message": str(e), "run_id": run_id}), 200
        else:
            return jsonify({"status": "error", "message": str(e), "run_id": run_id}), 500

#More functions from the template
import uuid

from datetime import datetime
import traceback
from google.cloud import firestore

import os
from datetime import timezone
from my_helpers.email_utils import send_email
from my_helpers.exceptions import handle_exception
from my_helpers.exceptions import (
    ExternalAPIError,
    MethodNotAllowedError,
    BadRequestError,
    BusinessRuleError,
 )
from my_helpers.notifications import send_push_notification
import json

# Initialize Firestore client once (shared across all flows)
database = firestore.Client()

# Firestore collection name for audit logs
AUDIT_COLLECTION = "flow_run_audit"


def send_error_email(run_id, flow_name, error_details):
    subject = f"Flow Error Alert - {flow_name} (Run ID: {run_id})"
    body = f"""\
An error occurred in flow '{flow_name}' (Run ID: {run_id}).

Error details:
{error_details}

Timestamp: {datetime.now(timezone.utc).isoformat()}

Please check the logs and Firestore audit collection for more details.
"""
    sender_email = "elnaz.razmi@wiseworks.be"
    sender_name = "Flow Alert"
    password = os.environ.get("EMAIL_PASSWORD")
    if not password:
        logging.error("EMAIL_PASSWORD environment variable is not set!")

    receiver_email = "razmielnaz@gmail.com"
    try:
        success = send_email(
            subject=subject,
            body=body,
            sender_email=sender_email,
            sender_name=sender_name,
            sender_password=password,
            recipient_email=receiver_email,
            recipient_cc=None,
            recipient_bcc=None,
            reply_to=None,
            attachment_bytes=None,
            attachment_filename=None,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
        )
        if not success:
            logging.error(
                f"❌ Failed to send error notification email for run {run_id}"
            )
    except Exception as ex:
        logging.error(
            f"❌ Exception occurred while sending error email for run {run_id}: {ex}",
            exc_info=True,
        )


def log_run_start(flow_name, run_id, start_time):
    doc_ref = database.collection(AUDIT_COLLECTION).document(run_id)
    try:
        doc_ref.set(
            {
                "flow_name": flow_name,
                "run_id": run_id,
                "start_time": start_time.isoformat(),
                "status": "Running",
                "steps": [],
            }
        )
    except Exception as ex:
        logging.error(
            f"❌ Failed to create Firestore doc for run {run_id}: {ex}", exc_info=True
        )


def log_step(run_id, step_name, status, logs=""):
    """
    Log an individual step of the flow to Firestore under the 'steps' array.
    """
    doc_ref = database.collection(AUDIT_COLLECTION).document(run_id)
    now = datetime.now(timezone.utc).isoformat()
    step_record = {
        "step_name": step_name,
        "status": status,
        "timestamp": now,
        "logs": logs,
    }
    try:
        doc_ref.update({"steps": firestore.ArrayUnion([step_record])})
    except Exception as ex:
        logging.error(
            f"❌ Failed to log step '{step_name}' for run {run_id}: {ex}", exc_info=True
        )


def log_run_end(run_id, end_time, status, error_details=None):
    doc_ref = database.collection(AUDIT_COLLECTION).document(run_id)
    update_data = {
        "end_time": end_time.isoformat(),
        "status": status,
    }
    if error_details:
        update_data["error_details"] = error_details
    try:
        doc_ref.update(update_data)
    except Exception as ex:
        logging.error(
            f"❌ Failed to update Firestore doc for run {run_id}: {ex}", exc_info=True
        )


# *************************************************************************************************************
# The wrapper: the main orchestrator:


def flow_with_audit_logging(flow_func, flow_name, *args, **kwargs):
    no_error = kwargs.get("no_error", "NO")
    print(">>>>>>>no_error in flow_with_audit_logging:", no_error)
    """Wrapper to audit any flow function run:
    - Creates unique run id
    - Logs run start in Firestore
    - Calls the flow function (passing run_id as kwarg if supported)
    - Logs run end or error with details
    - Sends error email if exception"""
    run_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)

    log_run_start(flow_name, run_id, start_time)

    try:
        # If flow_func accepts run_id, pass it
        if "run_id" in flow_func.__code__.co_varnames:
            # if 'run_id' in flow_func.__code__.co_varnames: is a Python way to check whether the function flow_func has a parameter named run_id.
            # Explanation:
            #   flow_func is a Python function object.
            #   Every function object has a __code__ attribute that contains the compiled bytecode details.
            #   __code__.co_varnames is a tuple of variable names (including parameters and locally defined variables) used in the function.
            #   The first N names in co_varnames represent the argument names, followed by local variables, etc.
            #    So checking for 'run_id' in co_varnames roughly tells you if "run_id" is one of the parameters or local variables the function declares.
            result = flow_func(*args, **kwargs, run_id=run_id)
            print("run result id run_id:", result)
        else:
            result = flow_func(*args, **kwargs)
            print("run result:", result)

        end_time = datetime.now(timezone.utc)
        log_step(
            run_id,
            step_name="end of flow",
            status="Finished",
            logs=result if isinstance(result, str) else str(result),
        )
        log_run_end(run_id, end_time, "Completed")
        return result
    except Exception as e:
        end_time = datetime.now(timezone.utc)
        error_trace = traceback.format_exc()
        log_run_end(run_id, end_time, "Error", error_details=error_trace)
        logging.error(
            f"Run {run_id} failed at {end_time.isoformat()} with error: {e}",
            exc_info=True,
        )
        # Fetch the run's document to get step info for email
        try:
            doc = database.collection(AUDIT_COLLECTION).document(run_id).get()
            # grabs the full data for a specific run (by unique run_id) from Firestore
            if doc.exists:
                data = doc.to_dict()
                steps = data.get("steps", [])
                # Find the last step with status "Failed"
                failed_step = None
                for step in reversed(steps):
                    # Reverse often used if you want to quickly find the last failed step without scanning from the very beginning of the list.
                    if step.get("status") == "Failed":
                        failed_step = step
                        break
                if failed_step:
                    step_name = failed_step.get("name")
                    step_logs = failed_step.get("logs")
                    # Enhance error details with step info
                    error_trace = f"Error occurred in step: '{step_name}'\nDetails: {step_logs}\n\nFull traceback:\n{error_trace}"
        except Exception as ex_fetch:
            logging.error(
                f"Failed to fetch run steps from Firestore for run {run_id}: {ex_fetch}",
                exc_info=True,
            )
        # fallback to just original error_trace without step info
        # Send notification email
        # send_error_email(run_id, flow_name, error_trace)
        # Return HTTP 500 error response
        message, status = handle_exception(e)
        if no_error == "YES":
            print("NO ERROR is enabled, returning 200 OK with error message.")
            push_notification_message = (
                f"Error handling the Billit webhook: {message}, 200 OK returned"
            )
            send_push_notification(push_notification_message)
            return (
                jsonify(
                    {
                        "error": f"{message}",
                        "details": str(e),
                        "failed_step": step_name if failed_step else None,
                        "step_logs": step_logs if failed_step else None,
                    }
                ),
                200,
            )
        print(f"NO ERROR is disabled, returning {status} NOK with error message.")
        push_notification_message = (
            f"Error handling the Billit webhook: {message}, {status} NOK returned"
        )
        send_push_notification(push_notification_message)
        return (
            jsonify(
                {
                    "error": f"{message}",
                    "details": str(e),
                    "failed_step": step_name if failed_step else None,
                    "step_logs": step_logs if failed_step else None,
                }
            ),
            status,
        )
