#!/usr/bin/python3
"""Test Bridges."""
import os

from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.request.overpass_request import OverpassQuery
from pretty_gpx.common.utils.asserts import assert_same_keys
from pretty_gpx.common.utils.paths import RUNNING_DIR
from pretty_gpx.rendering_modes.city.data.bridges import prepare_download_city_bridges
from pretty_gpx.rendering_modes.city.data.bridges import process_city_bridges


def __core_test_bridges(path: str, gt_names: set[str]) -> None:
    """Test Bridges."""
    # GIVEN
    gpx = GpxTrack.load(path)

    # WHEN
    query = OverpassQuery()
    prepare_download_city_bridges(query, gpx)
    query.launch_queries()
    bridges = process_city_bridges(query, gpx)
    # THEN
    assert_same_keys([b.name for b in bridges], gt_names)


def test_chicago_bridges() -> None:
    """Test Chicago Bridges."""
    __core_test_bridges(os.path.join(RUNNING_DIR, "marathon_chicago.gpx"),
                        {'William P. Fahey Bridge',
                         'State Street Bridge (Chicago)',
                         'Marshall Suloway Bridge',
                         'Wells Street Bridge',
                         'Adams Street Bridge',
                         'Cermak Road Bridge'})


def test_paris_bridges() -> None:
    """Test Paris Bridges."""
    __core_test_bridges(os.path.join(RUNNING_DIR, "10k_paris.gpx"),
                        {'Pont des Invalides',
                         'Pont du Carrousel'})


def test_new_york_bridges() -> None:
    """Test New York Bridges."""
    __core_test_bridges(os.path.join(RUNNING_DIR, "marathon_new_york.gpx"),
                        {"Madison Avenue Bridge",
                         "Pulaski Bridge",
                         "Willis Avenue Bridge",
                         "Queensboro Bridge",
                         "Verrazzano Bridge"})


def test_berlin_bridges() -> None:
    """Test Berlin Bridges."""
    __core_test_bridges(os.path.join(RUNNING_DIR, "marathon_berlin.gpx"),
                        {"Charlottenburger Brücke",
                         "Kronprinzenbrücke",
                         "Marchbrücke",
                         "Gotzkowskybrücke",
                         "Moltkebrücke",
                         "Michaelbrücke",
                         "Kottbusser Brücke",
                         "Potsdamer Brücke"})


def test_london_bridges() -> None:
    """Test London Bridges."""
    __core_test_bridges(os.path.join(RUNNING_DIR, "marathon_london.gpx"),
                        {"Tower Bridge"})


def test_bordeaux_bridges() -> None:
    """Test Bordeaux Bridges."""
    __core_test_bridges(os.path.join(RUNNING_DIR, "marathon_bordeaux.gpx"),
                        {"Pont de Pierre",
                         "Pont Jacques Chaban-Delmas"})
