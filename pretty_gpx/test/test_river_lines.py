"""Offline regression coverage for river centerline conversion."""
from types import SimpleNamespace

import pytest

from pretty_gpx.common.request.overpass_processing import get_rivers_polygons_from_lines


def river_result(ways):
    return SimpleNamespace(ways=[SimpleNamespace(nodes=[SimpleNamespace(lon=lon, lat=lat)
                                                        for lon, lat in coordinates])
                                for coordinates in ways])


@pytest.mark.parametrize('ways', [[], [[]], [[(0., 0.), (1., 1.)]]])
def test_no_usable_river_lines_returns_empty_list(ways) -> None:
    assert get_rivers_polygons_from_lines(river_result(ways), width=.001) == []


def test_multiple_river_lines_are_preserved() -> None:
    ways = [[(0., 0.), (.01, .01), (.02, 0.)],
            [(1., 0.), (1.01, .01), (1.02, 0.)]]
    polygons = get_rivers_polygons_from_lines(river_result(ways), width=.001)
    assert len(polygons) == 2
    assert all(polygon.is_valid and polygon.area > 0 for polygon in polygons)
