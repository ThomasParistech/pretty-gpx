#!/usr/bin/python3
"""Augmented GPX Data."""




from geopy.geocoders import Nominatim
from geopy.location import Location


def get_place_name(*, lon: float, lat: float) -> str:
    """Get the name of a place from its coordinates."""
    place_types = ["city", "town", "village", "locality", "hamlet"]

    geolocator = Nominatim(user_agent="Place-Guesser")
    location = geolocator.reverse((lat, lon), exactly_one=True)
    assert isinstance(location, Location)
    address = location.raw['address']

    for place_type in place_types:
        place_name = address.get(place_type, None)
        if place_name is not None:
            return place_name

    # for key, place_name in address.items():
    #     if key in place_types:
    #         return place_name

    raise RuntimeError(f"Place Not found at {lat:.3f}, {lon:.3f}. Got {address}")
