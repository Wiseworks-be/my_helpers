"""Error handling utilities."""
import logging

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