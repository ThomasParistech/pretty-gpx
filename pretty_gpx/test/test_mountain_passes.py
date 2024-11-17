#!/usr/bin/python3
"""Test Mountain Passes."""

import os

from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.utils.asserts import assert_same_keys
from pretty_gpx.common.utils.paths import CYCLING_DIR
from pretty_gpx.rendering_modes.mountain.data.mountain_augmented_gpx_data import get_close_mountain_passes
from pretty_gpx.rendering_modes.mountain.data.mountain_passes import prepare_download_mountain_passes
from pretty_gpx.rendering_modes.mountain.data.mountain_passes import process_mountain_passes


def __core_test_mountain_passes(path: str, gt_names: set[str]) -> None:
    """Test Mountain Passes."""
    # GIVEN
    gpx = GpxTrack.load(path)
    bounds = gpx.get_bounds()

    # WHEN
    query = OverpassQuery()
    prepare_download_mountain_passes(query, bounds)
    query.launch_queries()
    candidate_passes = process_mountain_passes(query, bounds)
    _, final_passes = get_close_mountain_passes(gpx, candidate_passes)

    # THEN
    assert_same_keys([b.name for b in final_passes], gt_names)


def test_marmotte_passes() -> None:
    """Test Marmotte Passes."""
    __core_test_mountain_passes(os.path.join(CYCLING_DIR, "marmotte.gpx"),
                                {'Col du Galibier',
                                 'Col du Télégraphe',
                                 'Col du Lautaret',
                                 'Col du Glandon',
                                 'Col de la Croix-de-Fer'})
