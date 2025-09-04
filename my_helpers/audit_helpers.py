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
