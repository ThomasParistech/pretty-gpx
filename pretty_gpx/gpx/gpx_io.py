#!/usr/bin/python3
"""Gpx I/O."""

import gpxpy
import gpxpy.gpx
from gpxpy.gpx import GPX
from natsort import natsorted

from pretty_gpx.utils.asserts import assert_isfile


def cast_to_list_gpx_path(list_gpx_path: str | bytes | list[str] | list[bytes]) -> list[str] | list[bytes]:
    """Casts the input GPX path(s) to a list and sorts the list if it contains paths."""
    if not isinstance(list_gpx_path, list):
        return [list_gpx_path]  # type: ignore

    if isinstance(list_gpx_path[0], str):
        list_gpx_path = natsorted(list_gpx_path)  # type: ignore

    return list_gpx_path  # type: ignore


def load_gpxpy(gpx_path: str | bytes) -> GPX:
    """Load GPX file."""
    if isinstance(gpx_path, str):
        assert_isfile(gpx_path, ext='.gpx')
        with open(gpx_path) as f:
            return gpxpy.parse(f)

    return gpxpy.parse(gpx_path)
