#!/usr/bin/python3
"""Matplotlib Utils."""

from types import TracebackType
from typing import Literal

import matplotlib


class MatplotlibBackend:
    """Context manager to temporarily change the Matplotlib backend.

    When generating a lot of plots that are directly saved as images instead of being displayed,
    it's convenient to switch to 'agg' instead of 'TkAgg' to prevent Matplotlib's cache from growing indefinitely
    """

    def __init__(self, backend_name: Literal["Agg", "TkAgg"]) -> None:
        self._previous_backend_name = matplotlib.get_backend()
        self._tmp_backend_name = backend_name

    def __enter__(self) -> None:
        matplotlib.use(self._tmp_backend_name)

    def __exit__(self,
                 exc_type: type[BaseException] | None,
                 exc_val: BaseException | None,
                 exc_tb: TracebackType | None) -> None:
        matplotlib.use(self._previous_backend_name)
