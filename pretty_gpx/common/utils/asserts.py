#!/usr/bin/python3
"""Asserts."""

import os
from collections.abc import Iterable
from collections.abc import Sized
from typing import Any
from typing import Final

import numpy as np

Number = float | int
Shape = tuple[int, ...] | list[int]
OptionalShape = tuple[int | None, ...] | list[int | None] | Shape

EPSILON: Final[float] = float(np.finfo(float).eps)


def _clean_msg(prefix: str = "") -> str:
    if prefix == "":
        return ""
    if prefix.endswith(":"):
        return prefix+" "
    if prefix.endswith(": "):
        return prefix
    return prefix+": "


def _shape_to_str(shape: OptionalShape) -> str:
    return ','.join([str(k) if k is not None else '?' for k in shape])


def assert_isfile(path: str, *, ext: str | None = None, msg: str = "") -> None:
    """Assert path corresponds to an existing file."""
    m = _clean_msg(msg)
    assert os.path.isfile(path), m+f"File doesn't exist: {path}"
    if ext is not None:
        assert path.endswith(ext), m+f"File doesn't have the expected '{ext}' extension: {path}"


def assert_isdir(path: str, *, msg: str = "") -> None:
    """Assert path corresponds to an existing directory."""
    m = _clean_msg(msg)

    if not os.path.isdir(path):
        error_msg = m+f"Folder doesn't exist: {path}"
        ext = os.path.splitext(path)[-1][1:].upper()  # Remove heading dot
        if ext != "":
            error_msg += f"\nThis path looks like a {ext} file instead of a directory"
        raise AssertionError(error_msg)


def assert_close(val1: Number, val2: Number, *, eps: float, msg: str = "") -> None:
    """Assert difference between two floats is smaller than a threshold."""
    m = _clean_msg(msg)
    assert np.abs(val1-val2) < eps, m+f" Expect difference to be smaller than {eps}. Got {np.abs(val1-val2)}"


def assert_neq(val1: Any, val2: Any, *, msg: str = "") -> None:
    """Assert non equality between two values."""
    m = _clean_msg(msg)
    assert val1 != val2, m+f"{val1 =} and {val2 =} are equal"


def assert_eq(val1: Any, val2: Any, *, msg: str = "") -> None:
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


def assert_np_dim(x: np.ndarray, dim: int, *, msg: str = "") -> None:
    """Assert Numpy array dimension."""
    m = _clean_msg(msg)
    assert x.ndim == dim, m+f"Invalid tensor. Expect dimension {dim}. Got {x.ndim}"


def assert_np_shape(x: np.ndarray, shape: OptionalShape, *, msg: str = "") -> None:
    """Assert Numpy array shape."""
    m = _clean_msg(msg)
    m += f"Invalid tensor. Must be of shape ({_shape_to_str(shape)}) and not {x.shape}"
    assert_np_dim(x, len(shape), msg=m)
    assert np.all([n1 == n2 or n2 is None for n1, n2 in zip(x.shape, shape)]), m


def assert_np_shape_endswith(x: np.ndarray, shape: OptionalShape, *, msg: str = "") -> None:
    """Assert Numpy array shape."""
    m = _clean_msg(msg)
    m += f"Invalid tensor. Must end with shape ({_shape_to_str(shape)}), but got {x.shape}"
    assert len(x.shape) >= len(shape), m
    assert np.all([n1 == n2 or n2 is None for n1, n2 in zip(x.shape[-len(shape):], shape)]), m


def assert_in(val: Any, a: dict[Any, Any] | Iterable[Any], *, msg: str = "") -> None:
    """Assert value is contained in sequence."""
    m = _clean_msg(msg)
    if isinstance(a, dict):
        a = a.keys()
    list_str = ',\n'.join(map(str, a))
    assert val in a, m+f"{val} is not in:\n{list_str}"


def assert_same_keys(a: dict[Any, Any] | Iterable[Any],
                     b: dict[Any, Any] | Iterable[Any],
                     *, sorted: bool = False, msg: str = "") -> None:
    """Assert dictionaries have the same keys."""
    m = _clean_msg(msg)

    if isinstance(a, dict):
        a = a.keys()
    if isinstance(b, dict):
        b = b.keys()

    set_a = set(a)
    set_b = set(b)

    unknown_names = list(set_a - set_b)
    missing_names = list(set_b - set_a)

    assert len(unknown_names) == len(missing_names) == 0, m+"Different keys.\n" \
        f"Keys in A but not in B: [{','.join(map(str, unknown_names))}]\n" \
        f"Keys in B but not in A: [{','.join(map(str, missing_names))}]"

    if sorted:
        assert_eq(list(a), list(b))


def assert_subset(a: dict[Any, Any] | Iterable[Any],
                  b: dict[Any, Any] | Iterable[Any],
                  *, msg: str = "") -> None:
    """Assert an iterable is a subset of another. A dictionary can be passed as well to check its keys."""
    m = _clean_msg(msg)

    keys_a = set(a.keys()) if isinstance(a, dict) else set(a)
    keys_b = set(b.keys()) if isinstance(b, dict) else set(b)

    new_values = list(keys_a - keys_b)

    assert len(new_values) == 0, m+f"Not a subset.\n Values in A but not in B: [{','.join(map(str, new_values))}]\n"
