import logging
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

_logging_configured = False

def get_logger(name: str = "saferide") -> logging.Logger:
    global _logging_configured
    if not _logging_configured:
        logging.basicConfig(
            level=LOG_LEVEL,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        _logging_configured = True
    return logging.getLogger(name)

