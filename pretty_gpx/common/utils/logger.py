#!/usr/bin/python3
"""Logger."""
import logging
import sys
from datetime import datetime
from typing import Final
from zoneinfo import ZoneInfo

DATE_TIME_FORMATING: Final[str] = "%Y/%m/%d - %H:%M:%S"


class Formatter(logging.Formatter):
    """Logger Formatter."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log."""
        record.levelname = record.levelname.upper()

        return super().format(record)

    @staticmethod
    def default() -> 'Formatter':
        """Default Formatter."""
        return Formatter('[ %(asctime)s | %(name)s | %(levelname)s ] %(message)s', DATE_TIME_FORMATING)

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:  # noqa: N802
        """Override formatTime to handle Paris timezone."""
        dt = datetime.fromtimestamp(record.created).astimezone(ZoneInfo("Europe/Paris"))
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime(DATE_TIME_FORMATING)

    @staticmethod
    def empty() -> 'Formatter':
        """Empty Formatter."""
        return Formatter("%(message)s")


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Set up a logger that can be reused across modules."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(Formatter.default())

    logger.addHandler(console_handler)

    return logger


# Create the default logger for reuse
logger = setup_logger("pretty-gpx")
