#!/usr/bin/python3
"""Pickle I/O."""
import pickle
from typing import Any


def write_pickle(file_path: str, obj: Any) -> None:
    """Write object to pickle file."""
    with open(file_path, 'wb') as f:
        pickle.dump(obj, f)


def read_pickle(file_path: str) -> Any:
    """Read object from pickle file."""
    with open(file_path, 'rb') as f:
        return pickle.load(f)
