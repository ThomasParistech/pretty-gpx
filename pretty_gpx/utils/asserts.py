#!/usr/bin/python3
"""Asserts."""

import os

import numpy as np

Number = float | int


def _clean_msg(prefix: str = "") -> str:
    if prefix == "":
        return ""
    if prefix.endswith(":"):
        return prefix+" "
    if prefix.endswith(": "):
        return prefix
    return prefix+": "


def assert_isfile(path: str, *, ext: str | None = None, msg: str = ""):
    """Assert path corresponds to an existing file."""
    m = _clean_msg(msg)
    assert os.path.isfile(path), m+f"File doesn't exist: {path}"
    if ext is not None:
        assert path.endswith(ext), m+f"File doesn't have the expected '{ext}' extension: {path}"


def assert_close(val1: Number, val2: Number, *, eps: float, msg: str = ""):
    """Assert difference between two floats is smaller than a threshold."""
    m = _clean_msg(msg)
    assert np.abs(val1-val2) < eps, m+f" Expect difference to be smaller than {eps}. Got {np.abs(val1-val2)}"


def assert_eq(val1: Number, val2: Number, *, msg: str = ""):
    """Assert equality between two  values."""
    m = _clean_msg(msg)
    assert val1 == val2, m+f" {val1 =} and {val2 =} are not equal"


def assert_lt(val1: Number, val2: Number, *, msg: str = ""):
    """Assert val1 < val2."""
    m = _clean_msg(msg)
    assert val1 < val2, m+f"Expect {val1 =} to be strictly lower than {val2 =}"


def assert_le(val1: Number, val2: Number, *, msg: str = ""):
    """Assert val1 <= val2."""
    m = _clean_msg(msg)
    assert val1 <= val2, m+f"Expect {val1 =} to be lower than {val2 =}"


def assert_gt(val1: Number, val2: Number, *, msg: str = ""):
    """Assert val1 > val2."""
    m = _clean_msg(msg)
    assert val1 > val2, m+f"Expect {val1 =} to be strictly greater than {val2 =}"


def assert_ge(val1: Number, val2: Number, *, msg: str = ""):
    """Assert val1 >= val2."""
    m = _clean_msg(msg)
    assert val1 >= val2, m+f"Expect {val1 =} to be greater than {val2 =}"
