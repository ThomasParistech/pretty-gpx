#!/usr/bin/python3
"""Test Bridges."""

import os

from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.utils.asserts import assert_same_keys
from pretty_gpx.common.utils.paths import RUNNING_DIR
from pretty_gpx.rendering_modes.city.data.bridges import get_gpx_track_bridges
from pretty_gpx.rendering_modes.city.data.bridges import prepare_download_city_bridges
from pretty_gpx.rendering_modes.city.data.bridges import process_city_bridges


def __core_test_bridges(path: str, gt_names: set[str]) -> None:
    """Test Bridges."""
    # GIVEN
    gpx = GpxTrack.load(path)
    bounds = gpx.get_bounds()

    # WHEN
    query = OverpassQuery()
    prepare_download_city_bridges(query, bounds)
    query.launch_queries()
    bridges, names = process_city_bridges(query, bounds)
    final_bridges = get_gpx_track_bridges(bridges, names, gpx)

    # THEN
    assert_same_keys([b.name for b in final_bridges], gt_names)


def test_chicago_bridges() -> None:
    """Test Chicago Bridges."""
    __core_test_bridges(os.path.join(RUNNING_DIR, "marathon_chicago.gpx"),
                        {'BP Bridge',
                         'William P. Fahey Bridge',
                         'Bataan-Corregidor Memorial Bridge',
                         'Marshall Suloway Bridge',
                         'Wells Street Bridge',
                         'Adams Street Bridge',
                         'Cermak Road Bridge'})


def test_paris_bridges() -> None:
    """Test Paris Bridges."""
    __core_test_bridges(os.path.join(RUNNING_DIR, "10k_paris.gpx"),
                        {'Pont des Invalides',
                         'Pont du Carrousel'})
