from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from src.utils.paths import ensure_dir, logs_dir


_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str = "file_splitter") -> logging.Logger:
    """
    Initialize and return the root application logger.
    Creates a timestamped log file under logs/ and adds a console handler.
    """
    log_dir = ensure_dir(logs_dir())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"execution_{timestamp}.log"

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        logger.addHandler(file_handler)

    return logger


def get_logger(module: str = "file_splitter") -> logging.Logger:
    """Return a child logger for the given module name."""
    return logging.getLogger(module)
