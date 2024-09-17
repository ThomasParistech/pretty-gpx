#!/usr/bin/python3
"""Log Scope."""

import time

from pretty_gpx.common.utils.logger import logger


class LogScopeTime:
    """Log the time spent inside a scope. Use as context `with LogScopeTime(name):`."""

    def __init__(self, name: str):
        self._name = name

    def __enter__(self):
        self._start_time = time.perf_counter()
        logger.info(self._name)

    def __exit__(self, exception_type, exception_value, exception_traceback):
        end_time = time.perf_counter()
        logger.info(f"--- {(end_time - self._start_time): .2f} s ({self._name}) ---")
