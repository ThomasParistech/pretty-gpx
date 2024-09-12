#!/usr/bin/python3
"""Utils."""

import os
from typing import TypeVar
import datetime

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


def suffix_filename(filepath: str, suffix: str) -> str:
    """Add a suffix to a file path.

    Args:
        filepath: The file path
        suffix: The suffix to add to the file path

    Returns:
        The file path with the suffix added
    """
    base, ext = os.path.splitext(filepath)
    return f"{base}{suffix}{ext}"

def format_timedelta(total_seconds: float | int) -> str:
    """Format the timedelta to a string"""

    # Extract days, hours, minutes, and seconds
    days, remainder = divmod(total_seconds, 86400)  # 86400 seconds in a day
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d-")
    if hours > 0 or days > 0:  # Show hours if days are shown or hours are non-zero
        if days > 0:
            parts.append(f"{hours:2.0f}h")
        else:
            parts.append(f"{hours}h")
    if minutes > 0 or hours > 0 or days > 0:  # Show minutes if hours or days are shown or minutes are non-zero
        if days > 0 or hours > 0:
            parts.append(f"{minutes:2.0f}")
        else:
            parts.append(f"{minutes}min")
    if seconds > 0 or minutes > 0 or hours > 0 or days > 0:  # Show seconds if any higher units are shown or seconds are non-zero
        if not(days > 0 or hours > 0):
            parts.append(f"{seconds:2.0f}")
    
    # Join the parts with commas
    return ''.join(parts) if parts else '0s'
