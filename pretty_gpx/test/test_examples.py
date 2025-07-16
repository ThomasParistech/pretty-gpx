#!/usr/bin/python3
"""Test Examples."""
import os

from pretty_gpx.common.data.examples import CyclingGpx
from pretty_gpx.common.data.examples import HikingGpx
from pretty_gpx.common.data.examples import RunningGpx
from pretty_gpx.common.utils.asserts import assert_isfile
from pretty_gpx.common.utils.asserts import assert_same_keys


def __core_test_examples(gpx_enum: type[HikingGpx] | type[RunningGpx] | type[CyclingGpx]) -> None:
    """Test that the enumeration contains all the GPX files."""
    paths = [gpx_enum_item.path for gpx_enum_item in gpx_enum]
    existing_filenames = [f.name for f in os.scandir(gpx_enum.folder()) if f.is_file()]

    assert_same_keys([os.path.basename(p) for p in paths], existing_filenames)

    for p in paths:
        assert_isfile(p, ext='.gpx')


def test_cycling_examples() -> None:
    """Test Cycling GPX examples."""
    __core_test_examples(CyclingGpx)


def test_hiking_examples() -> None:
    """Test Hiking GPX examples."""
    __core_test_examples(HikingGpx)


def test_running_examples() -> None:
    """Test Running GPX examples."""
    __core_test_examples(RunningGpx)
