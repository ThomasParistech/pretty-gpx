#!/usr/bin/python3
"""Utils."""

import os
from typing import TypeVar

import numpy as np

T = TypeVar('T')


def safe(value: T | None) -> T:
    """Assert value is not None."""
    assert value is not None
    return value


def mm_to_inch(mm: float) -> float:
    """Convert Millimeters to Inches."""
    return mm/25.4


def mm_to_point(mm: float) -> float:
    """Convert Millimeter to Matplotlib point size."""
    return 72*mm_to_inch(mm)


def assert_isfile(path: str, ext: str | None = None):
    """Assert path corresponds to an existing file."""
    assert os.path.isfile(path), f"File doesn't exist: {path}"
    if ext is not None:
        assert path.endswith(ext), f"File doesn't have the expected '{ext}' extension: {path}"


def assert_close(val1: float | int, val2: float | int, *, eps: float, msg: str = ""):
    """Assert difference between two floats is smaller than a threshold."""
    assert np.abs(val1-val2) < eps, msg+f" Expect difference to be smaller than {eps}. Got {np.abs(val1-val2)}"
