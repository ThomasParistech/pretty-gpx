#!/usr/bin/python3
"""Asserts."""

import os
from typing import Any

import numpy as np


def assert_isfile(path: str, ext: str | None = None):
    """Assert path corresponds to an existing file."""
    assert os.path.isfile(path), f"File doesn't exist: {path}"
    if ext is not None:
        assert path.endswith(ext), f"File doesn't have the expected '{ext}' extension: {path}"


def assert_close(val1: float | int, val2: float | int, *, eps: float, msg: str = ""):
    """Assert difference between two floats is smaller than a threshold."""
    assert np.abs(val1-val2) < eps, msg+f" Expect difference to be smaller than {eps}. Got {np.abs(val1-val2)}"


def assert_eq(val1: Any, val2: Any, *, msg: str = ""):
    """Assert equality between two  values."""
    assert val1 == val2, msg+f" {val1 =} and {val2 =} are not equal"
