#!/usr/bin/python3
"""Utils."""

import os
from typing import TypeVar

EARTH_RADIUS_M = 6371000
MAX_RECURSION_DEPTH = 100  # sys.getrecursionlimit() - 10

T = TypeVar('T')


def get(value: T | None, default: T) -> T:
    """Get value or default if value is None."""
    return default if value is None else value


def safe(value: T | None) -> T:
    """Assert value is not None."""
    assert value is not None
    return value


def str_to_float(s: str) -> float | None:
    """Convert a string to a float."""
    try:
        return float(s)
    except ValueError:
        return None


def str_to_int(s: str) -> int | None:
    """Convert a string to an integer."""
    f = str_to_float(s)
    return None if f is None else int(f)


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


def are_close(ref: float, var: float, *, eps: float = 1e-3) -> bool:
    """Get if the two floats are closer than the input epsilon."""
    return abs(var-ref) < eps


def format_timedelta(total_seconds: float | int) -> str:
    """Format the timedelta to a string."""
    # Extract days, hours, minutes, and seconds
    days, remainder = divmod(total_seconds, 86400)  # 86400 seconds in a day
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d-")
    # Show hours if days are shown or hours are non-zero
    if hours > 0 or days > 0:
        if days > 0:
            parts.append(f"{hours:2.0f}h")
        else:
            parts.append(f"{hours:.0f}h")
    # Show minutes if hours or days are shown or minutes are non-zero
    if minutes > 0 or hours > 0 or days > 0:
        if days > 0 or hours > 0:
            parts.append(f"{minutes:02.0f}" if minutes != 0 else "00")
        else:
            parts.append(f"{minutes:.0f}min")
    # Show seconds if any higher units are shown or seconds are non-zero
    if seconds > 0 or minutes > 0 or hours > 0 or days > 0:
        if not (days > 0 or hours > 0):
            parts.append(f"{seconds:02.0f}" if seconds != 0 else "00")

    # Join the parts with commas
    return ''.join(parts) if parts else '0s'


def points_are_close(p1: tuple[float, float], p2: tuple[float, float], eps: float = 1e-5) -> bool:
    """Get if points are closed with a tolerance epsilon."""
    return are_close(p1[0], p2[0], eps=eps) and are_close(p1[1], p2[1], eps=eps)


def convert_bytes(size_bytes: int) -> str:
    """Convert bytes to the most appropriate unit (KB, MB, or GB)."""
    if size_bytes < 1000 ** 2:
        return f"{size_bytes / 1000:.2f} KB"
    elif size_bytes < 1000 ** 3:
        return f"{size_bytes / (1000 ** 2):.2f} MB"
    else:
        return f"{size_bytes / (1000 ** 3):.2f} GB"
