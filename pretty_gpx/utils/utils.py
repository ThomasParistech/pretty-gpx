#!/usr/bin/python3
"""Utils."""

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
