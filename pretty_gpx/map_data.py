#!/usr/bin/python3
"""Map Data."""
from dataclasses import dataclass
from typing import List
from typing import Tuple

import numpy as np
import overpy
from geopy.geocoders import Nominatim
from geopy.location import Location
from gpx_bounds import GpxBounds
from gpx_track import GpxTrack
from gpx_track import local_m_to_deg


@dataclass
class MountainPass:
    """Mountain pass Data."""
    name: str
    ele: float  # Elevation (in m)
    lon: float
    lat: float


def get_close_mountain_passes(gpx: GpxTrack, max_dist_m: float) -> Tuple[List[int], List[MountainPass]]:
    """aaaaa"""
    max_dist_deg = local_m_to_deg(max_dist_m)
    gpx_curve = np.stack((gpx.list_lat, gpx.list_lon), axis=-1)

    # Request local mountain passes
    api = overpy.Overpass()
    bounds = GpxBounds.from_list(list_lon=gpx.list_lon,
                                 list_lat=gpx.list_lat).add_relative_margin(0.1)
    bounds_str = f"({bounds.lat_min:.2f}, {bounds.lon_min:.2f}, {bounds.lat_max:.2f}, {bounds.lon_max:.2f})"
    result = api.query(f"""(
        nwr["natural"="saddle"]{bounds_str};
        nwr["mountain_pass"="yes"]{bounds_str};
    );
    out body;""")

    ids: List[int] = []
    passes: List[MountainPass] = []
    for node in result.nodes:
        lon, lat = float(node.lon), float(node.lat)
        tags = node.tags
        if "name" in tags and "ele" in tags:
            name, ele = str(node.tags["name"]), float(node.tags["ele"])
            distances = np.linalg.norm(gpx_curve - np.array((lat, lon)), axis=-1)
            closest_idx = int(np.argmin(distances))
            closest_distance = distances[closest_idx]

            if closest_distance < max_dist_deg:
                ids.append(closest_idx)
                passes.append(MountainPass(ele=ele, name=name, lon=lon, lat=lat))

    return ids, passes


def is_close_to_a_mountain_pass(lon: float, lat: float,
                                mountain_passes: List[MountainPass],
                                max_dist_m: float) -> bool:
    """aaaaaaaa"""
    distances = np.linalg.norm(np.array([lat, lon]) - np.array([[m.lat, m.lon]
                                                                for m in mountain_passes]), axis=-1)
    return np.min(distances) < local_m_to_deg(max_dist_m)


def get_place_name(lon: float, lat: float) -> str:
    """aaaaa"""
    place_types = ["city", "town", "village", "locality", "hamlet"]

    geolocator = Nominatim(user_agent="Place-Guesser")
    location = geolocator.reverse((lat, lon), exactly_one=True)
    assert isinstance(location, Location)
    address = location.raw['address']

    for place_type in place_types:
        place_name = address.get(place_type, None)
        if place_name:
            return place_name

    raise RuntimeError("Place Not found")
