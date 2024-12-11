#!/usr/bin/python3
"""Test Markers."""
from pretty_gpx.common.drawing.plt_marker import MarkerType
from pretty_gpx.common.utils.asserts import assert_not_empty


def test_markers() -> None:
    """Test Markers."""
    for marker in MarkerType:
        path = marker.path()
        assert_not_empty(path)
