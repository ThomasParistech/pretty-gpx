#!/usr/bin/python3
"""Utils."""

import os
from typing import TypeVar

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
