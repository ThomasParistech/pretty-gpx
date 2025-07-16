#!/usr/bin/python3
"""Test Mountain Huts."""

from pretty_gpx.common.data.examples import HikingGpx
from pretty_gpx.common.gpx.multi_gpx_track import MultiGpxTrack
from pretty_gpx.common.request.overpass_request import OverpassQuery
from pretty_gpx.common.utils.asserts import assert_same_keys
from pretty_gpx.rendering_modes.multi_mountain.data.mountain_huts import prepare_download_mountain_huts
from pretty_gpx.rendering_modes.multi_mountain.data.mountain_huts import process_mountain_huts


def __core_test_mountain_huts(scenes: list[HikingGpx], gt_names: set[str]) -> None:
    """Test Mountain Huts."""
    # GIVEN
    gpx = MultiGpxTrack.load([scene.path for scene in scenes])

    # WHEN
    query = OverpassQuery()
    prepare_download_mountain_huts(query, gpx)
    query.launch_queries()
    huts = process_mountain_huts(query, gpx)

    # THEN
    assert_same_keys([b.name for b in huts], gt_names)


def test_vanoise_huts() -> None:
    """Test Vanoise Huts."""
    __core_test_mountain_huts([HikingGpx.VANOISE_1,
                               HikingGpx.VANOISE_2,
                               HikingGpx.VANOISE_3],
                              {"Refuge d'Entre Deux Eaux",
                               "Refuge de Plan Sec"})
