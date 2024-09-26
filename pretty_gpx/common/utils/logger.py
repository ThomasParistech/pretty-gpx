#!/usr/bin/python3
"""Logger."""
import logging
import sys


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Set up a logger that can be reused across modules."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('[ %(asctime)s | %(name)s | %(levelname)s ] %(message)s',
                                                   "%Y/%m/%d - %H:%M:%S"))

    logger.addHandler(console_handler)

    return logger


# Create the default logger for reuse
logger = setup_logger("pretty-gpx")
