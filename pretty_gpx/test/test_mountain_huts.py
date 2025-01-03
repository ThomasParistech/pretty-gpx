#!/usr/bin/python3
"""Test Mountain Huts."""
import os

from pretty_gpx.common.gpx.multi_gpx_track import MultiGpxTrack
from pretty_gpx.common.request.overpass_request import OverpassQuery
from pretty_gpx.common.utils.asserts import assert_same_keys
from pretty_gpx.common.utils.paths import HIKING_DIR
from pretty_gpx.rendering_modes.multi_mountain.data.mountain_huts import prepare_download_mountain_huts
from pretty_gpx.rendering_modes.multi_mountain.data.mountain_huts import process_mountain_huts


def __core_test_mountain_huts(paths: list[str], gt_names: set[str]) -> None:
    """Test Mountain Huts."""
    # GIVEN
    gpx = MultiGpxTrack.load(paths)

    # WHEN
    query = OverpassQuery()
    prepare_download_mountain_huts(query, gpx)
    query.launch_queries()
    huts = process_mountain_huts(query, gpx)

    # THEN
    assert_same_keys([b.name for b in huts], gt_names)


def test_vanoise_huts() -> None:
    """Test Vanoise Huts."""
    __core_test_mountain_huts([os.path.join(HIKING_DIR, "vanoise1.gpx"),
                               os.path.join(HIKING_DIR, "vanoise2.gpx"),
                               os.path.join(HIKING_DIR, "vanoise3.gpx")],
                              {"Refuge d'Entre Deux Eaux",
                               "Refuge de Plan Sec"})
