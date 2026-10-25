#!/usr/bin/python3
"""Offline regression tests for reverse-geocoded place names."""

from unittest.mock import patch

import pytest
from geopy.location import Location

from pretty_gpx.common.data.place_name import get_place_name


@pytest.mark.parametrize(('address', 'expected'), [
    ({'road': 'Example Road', 'municipality': 'Example Municipality',
      'country': 'Example Country'}, 'Example Municipality'),
    ({'city': 'City', 'municipality': 'Municipality'}, 'City'),
    ({'town': 'Town', 'municipality': 'Municipality'}, 'Town'),
    ({'village': 'Village', 'municipality': 'Municipality'}, 'Village'),
    ({'locality': 'Locality', 'municipality': 'Municipality'}, 'Locality'),
    ({'hamlet': 'Hamlet', 'municipality': 'Municipality'}, 'Hamlet'),
])
def test_place_name(address: dict[str, str], expected: str) -> None:
    """Accept municipalities while preserving existing place-name priorities."""
    location = Location(expected, (0.0, 0.0), {'address': address})
    with patch('pretty_gpx.common.data.place_name.Nominatim') as geocoder:
        geocoder.return_value.reverse.return_value = location
        assert get_place_name(lon=0.0, lat=0.0) == expected
        geocoder.return_value.reverse.assert_called_once_with((0.0, 0.0), exactly_one=True)
