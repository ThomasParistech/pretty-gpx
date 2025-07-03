#!/usr/bin/python3
"""Place Name."""

from geopy.geocoders import Nominatim
from geopy.location import Location

from pretty_gpx.common.drawing.utils.scatter_point import ScatterPoint
from pretty_gpx.common.drawing.utils.scatter_point import ScatterPointCategory
from pretty_gpx.common.gpx.gpx_distance import get_distance_m
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.gpx.multi_gpx_track import MultiGpxTrack
from pretty_gpx.common.utils.profile import profile


@profile
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


def get_start_end_named_points(gpx_track: GpxTrack | MultiGpxTrack) -> list[ScatterPoint]:
    """Get the start and end names of a GPX track."""
    if isinstance(gpx_track, GpxTrack):
        start_lon, start_lat = gpx_track.list_lon[0], gpx_track.list_lat[0]
        end_lon, end_lat = gpx_track.list_lon[-1], gpx_track.list_lat[-1]
    else:
        start_lon, start_lat = gpx_track.tracks[0].list_lon[0], gpx_track.tracks[0].list_lat[0]
        end_lon, end_lat = gpx_track.tracks[-1].list_lon[-1], gpx_track.tracks[-1].list_lat[-1]

    start = ScatterPoint(name=get_place_name(lon=start_lon, lat=start_lat),
                         lon=start_lon,
                         lat=start_lat,
                         category=ScatterPointCategory.START)
    end = ScatterPoint(name=get_place_name(lon=end_lon, lat=end_lat),
                       lon=end_lon,
                       lat=end_lat,
                       category=ScatterPointCategory.END)

    if get_distance_m(lonlat_1=(start_lon, start_lat),
                      lonlat_2=(end_lon, end_lat)) < 1000:
        name = get_place_name(lon=end_lon, lat=end_lat)
        if name != start.name:
            end.name = name

    return [start, end]
