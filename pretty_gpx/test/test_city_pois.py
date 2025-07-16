#!/usr/bin/python3
"""Test City Points of Interest."""


from pretty_gpx.common.data.examples import RunningGpx
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.request.overpass_request import OverpassQuery
from pretty_gpx.common.utils.asserts import assert_subset
from pretty_gpx.rendering_modes.city.data.city_pois import prepare_download_city_pois
from pretty_gpx.rendering_modes.city.data.city_pois import process_city_pois


def __core_test_city_pois(scene: RunningGpx, gt_required_names: set[str]) -> None:
    """Test City Points of Interest, focusing on the most relevant ones as others may vary with the implementation."""
    # GIVEN
    gpx = GpxTrack.load(scene.path)

    # WHEN
    query = OverpassQuery()
    prepare_download_city_pois(query, gpx)
    query.launch_queries()
    pois = process_city_pois(query, gpx)

    # THEN
    assert_subset(gt_required_names, [b.name for b in pois])


def test_london_city_pois() -> None:
    """Test London City Points of Interest."""
    __core_test_city_pois(RunningGpx.MARATHON_LONDON,
                          {"Tower of London",
                           "Saint Paul's",
                           "Westminster Abbey",
                           "The Monument",
                           "Buckingham Palace"})


def test_paris_city_pois() -> None:
    """Test Paris City Points of Interest."""
    __core_test_city_pois(RunningGpx.TEN_K_PARIS,
                          {"Musée d'Orsay",
                           'Palais du Louvre',
                           'Opéra Garnier',
                           'Assemblée nationale',
                           'Grand Palais'})
