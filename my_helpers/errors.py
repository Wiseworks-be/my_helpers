"""Error handling utilities."""
import logging


# webhook

def check_mandatory_args(args: dict):
    """
    Checks that all mandatory function arguments are provided (not None or empty).
    Raises ValueError listing which arguments are missing.
    """
    missing = [k for k, v in args.items() if not v]
    if missing:
        msg = f"Mandatory function argument(s) missing: {', '.join(missing)}"
        raise ValueError(msg)  # Using ValueError instead of custom exception