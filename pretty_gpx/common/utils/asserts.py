#!/usr/bin/python3
"""Asserts."""

import os
from collections.abc import Iterable
from collections.abc import Sized
from typing import Final

import numpy as np

Number = float | int

EPSILON: Final[float] = float(np.finfo(float).eps)


def _clean_msg(prefix: str = "") -> str:
    if prefix == "":
        return ""
    if prefix.endswith(":"):
        return prefix+" "
    if prefix.endswith(": "):
        return prefix
    return prefix+": "


def assert_isfile(path: str, *, ext: str | None = None, msg: str = "") -> None:
    """Assert path corresponds to an existing file."""
    m = _clean_msg(msg)
    assert os.path.isfile(path), m+f"File doesn't exist: {path}"
    if ext is not None:
        assert path.endswith(ext), m+f"File doesn't have the expected '{ext}' extension: {path}"


def assert_close(val1: Number, val2: Number, *, eps: float, msg: str = "") -> None:
    """Assert difference between two floats is smaller than a threshold."""
    m = _clean_msg(msg)
    assert np.abs(val1-val2) < eps, m+f" Expect difference to be smaller than {eps}. Got {np.abs(val1-val2)}"


def assert_eq(val1: Number, val2: Number, *, msg: str = "") -> None:
    """Assert equality between two  values."""
    m = _clean_msg(msg)
    assert val1 == val2, m+f" {val1 =} and {val2 =} are not equal"


def assert_float_eq(val1: Number, val2: Number, *, msg: str = "") -> None:
    """Assert equality between two float values."""
    assert_close(val1, val2, eps=EPSILON, msg=msg)


def assert_lt(val1: Number, val2: Number, *, msg: str = "") -> None:
    """Assert val1 < val2."""
    m = _clean_msg(msg)
    assert val1 < val2, m+f"Expect {val1 =} to be strictly lower than {val2 =}"


def assert_le(val1: Number, val2: Number, *, msg: str = "") -> None:
    """Assert val1 <= val2."""
    m = _clean_msg(msg)
    assert val1 <= val2, m+f"Expect {val1 =} to be lower than {val2 =}"


def assert_gt(val1: Number, val2: Number, *, msg: str = "") -> None:
    """Assert val1 > val2."""
    m = _clean_msg(msg)
    assert val1 > val2, m+f"Expect {val1 =} to be strictly greater than {val2 =}"


def assert_ge(val1: Number, val2: Number, *, msg: str = "") -> None:
    """Assert val1 >= val2."""
    m = _clean_msg(msg)
    assert val1 >= val2, m+f"Expect {val1 =} to be greater than {val2 =}"


def assert_in_range(val: Number, mini: Number, maxi: Number, *, msg: str = "") -> None:
    """Assert mini <= val <= maxi."""
    m = _clean_msg(msg)
    assert mini <= val <= maxi, m+f"Expect {val} to be inside [{mini}, {maxi}]"


def assert_in_strict_range(val: Number, mini: Number, maxi: Number, *, msg: str = "") -> None:
    """Assert mini < val < maxi."""
    m = _clean_msg(msg)
    assert mini < val < maxi, m+f"Expect {val} to be inside [{mini}, {maxi}]"


def assert_len(seq: Sized, size: int, *, msg: str = "") -> None:
    """Assert Python list has expected length."""
    m = _clean_msg(msg)
    assert len(seq) == size, m+f"Expect sequence of length {size}. Got length {len(seq)}."


def assert_same_len(seqs: Iterable[Sized], size: int | None = None, *,  msg: str = "") -> None:
    """Assert all Python lists have the same length."""
    m = _clean_msg(msg)
    lengths = set(len(seq) for seq in seqs)
    assert len(lengths) == 1, m+f"Expect sequences of same lengths. Got lengths {lengths}."
    if size is not None:
        common_length = list(lengths)[0]
        assert common_length == size,  m+f"Expect sequences of length {size}. Got {common_length}."


def assert_not_empty(seq: Sized, *, msg: str = "") -> None:
    """Assert Sized element is not empty."""
    m = _clean_msg(msg)
    assert len(seq) != 0, m+"Got empty sequence."
