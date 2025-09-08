"""Error handling utilities."""
import logging

# Logger setup
def setup_logger(name, level="INFO"):
    """Setup a basic logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

def log_error(message, logger_name="my-helpers"):
    """Quick error logging function."""
    logger = setup_logger(logger_name)
    logger.error(message)
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