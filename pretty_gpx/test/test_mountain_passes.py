#!/usr/bin/python3
"""Test Mountain Passes."""


from pretty_gpx.common.data.examples import CyclingGpx
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.request.overpass_request import OverpassQuery
from pretty_gpx.common.utils.asserts import assert_same_keys
from pretty_gpx.rendering_modes.mountain.data.mountain_passes import prepare_download_mountain_passes
from pretty_gpx.rendering_modes.mountain.data.mountain_passes import process_mountain_passes


def __core_test_mountain_passes(scene: CyclingGpx, gt_names: set[str]) -> None:
    """Test Mountain Passes."""
    # GIVEN
    gpx = GpxTrack.load(scene.path)

    # WHEN
    query = OverpassQuery()
    prepare_download_mountain_passes(query, gpx)
    query.launch_queries()
    passes = process_mountain_passes(query, gpx)

    # THEN
    assert_same_keys([b.name for b in passes], gt_names)


def test_marmotte_passes() -> None:
    """Test Marmotte Passes."""
    __core_test_mountain_passes(CyclingGpx.MARMOTTE,
                                {'Col du Galibier\n(2642 m)',
                                 'Col du Télégraphe\n(1566 m)',
                                 'Col du Lautaret\n(2058 m)',
                                 'Col du Glandon\n(1924 m)',
                                 'Col de la Croix-de-Fer\n(2067 m)'})
