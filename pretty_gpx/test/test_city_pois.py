#!/usr/bin/python3
"""Test City Points of Interest."""

import os

from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.utils.asserts import assert_subset
from pretty_gpx.common.utils.paths import RUNNING_DIR
from pretty_gpx.rendering_modes.city.data.city_pois import get_gpx_track_city_pois
from pretty_gpx.rendering_modes.city.data.city_pois import prepare_download_city_pois
from pretty_gpx.rendering_modes.city.data.city_pois import process_city_pois
from pretty_gpx.rendering_modes.city.drawing.city_drawer import CityDrawingInputs


def __core_test_city_pois(path: str, gt_required_names: set[str]) -> None:
    """Test City Points of Interest, focusing on the most relevant ones as others may vary with the implementation."""
    # GIVEN
    paper = PAPER_SIZES["A4"]
    gpx = GpxTrack.load(path)
    bounds = gpx.get_bounds()
    _, layout = CityDrawingInputs.build_stats_text(stats_items=["a", "b", "c"])
    _, paper_fig = layout.get_download_bounds_and_paper_figure(gpx, paper)

    # WHEN
    query = OverpassQuery()
    prepare_download_city_pois(query, bounds)
    query.launch_queries()
    candidate_pois = process_city_pois(query, bounds)

    final_pois = get_gpx_track_city_pois(candidate_pois, gpx, paper_fig)

    # THEN
    assert_subset(gt_required_names, [b.name for b in final_pois])


def test_london_city_pois() -> None:
    """Test London City Points of Interest."""
    __core_test_city_pois(os.path.join(RUNNING_DIR, "marathon_london.gpx"),
                          {"Tower of London",
                           "St Paul's Cathedral",
                           "Westminster Abbey",
                           "Buckingham Palace"})


def test_paris_city_pois() -> None:
    """Test Paris City Points of Interest."""
    __core_test_city_pois(os.path.join(RUNNING_DIR, "10k_paris.gpx"),
                          {"Musée d'Orsay",
                           'Palais du Louvre',
                           'Opéra Garnier',
                           'Assemblée nationale',
                           'Grand Palais'})
