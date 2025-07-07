import logging
import os
from logging.handlers import RotatingFileHandler

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

_logging_configured = False

def _ensure_log_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def get_logger(name: str = "saferide") -> logging.Logger:
    global _logging_configured
    if not _logging_configured:
        _ensure_log_dir(LOG_FILE)
        handlers = [
            logging.StreamHandler(),
            RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3),
        ]
        logging.basicConfig(
            level=LOG_LEVEL,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=handlers,
        )
        _logging_configured = True
    return logging.getLogger(name)

