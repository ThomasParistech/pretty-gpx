#!/usr/bin/python3
"""Map Data."""
from dataclasses import dataclass
from typing import BinaryIO
from typing import TextIO

import numpy as np
import overpy
from geopy.geocoders import Nominatim
from geopy.location import Location

from pretty_gpx.gpx.gpx_bounds import GpxBounds
from pretty_gpx.gpx.gpx_track import GpxTrack
from pretty_gpx.gpx.gpx_track import local_m_to_deg


@dataclass
class MountainPass:
    """Mountain pass Data."""
    name: str
    ele: float  # Elevation (in m)
    lon: float
    lat: float


@dataclass
class AugmentedGpxData:
    """aaaaa"""
    track: GpxTrack
    dist_km: float
    uphill_m: float

    start_name: str | None
    end_name: str | None

    is_closed: bool

    mountain_passes: list[MountainPass]
    passes_ids: list[int]

    @staticmethod
    def from_path(gpx_path: str | BinaryIO | TextIO | bytes,
                  strict_ths_m: float = 50,
                  loose_ths_m: float = 1000) -> 'AugmentedGpxData':
        """aaaaa"""
        gpx_track, dist_km, uphill_m = GpxTrack.load(gpx_path)

        is_closed = gpx_track.is_closed(loose_ths_m)
        passes_ids, mountain_passes = get_close_mountain_passes(gpx_track, strict_ths_m)
        close_to_start = is_close_to_a_mountain_pass(lon=gpx_track.list_lon[0],
                                                     lat=gpx_track.list_lat[0],
                                                     mountain_passes=mountain_passes,
                                                     max_dist_m=loose_ths_m)
        close_to_end = is_close_to_a_mountain_pass(lon=gpx_track.list_lon[-1],
                                                   lat=gpx_track.list_lat[-1],
                                                   mountain_passes=mountain_passes,
                                                   max_dist_m=loose_ths_m)

        if close_to_start:
            start_name = None
        else:
            start_name = get_place_name(lon=gpx_track.list_lon[0], lat=gpx_track.list_lat[0])

        if close_to_end or is_closed:
            end_name = None
        else:
            end_name = get_place_name(lon=gpx_track.list_lon[-1], lat=gpx_track.list_lat[-1])

        return AugmentedGpxData(track=gpx_track,
                                dist_km=dist_km,
                                uphill_m=uphill_m,
                                start_name=start_name,
                                end_name=end_name,
                                is_closed=is_closed,
                                mountain_passes=mountain_passes,
                                passes_ids=passes_ids)


def get_close_mountain_passes(gpx: GpxTrack, max_dist_m: float) -> tuple[list[int], list[MountainPass]]:
    """Get mountain passes close to a GPX track."""
    max_dist_deg = local_m_to_deg(max_dist_m)
    gpx_curve = np.stack((gpx.list_lat, gpx.list_lon), axis=-1)

    # Request local mountain passes
    # See https://wiki.openstreetmap.org/wiki/Key:natural
    # See https://wiki.openstreetmap.org/wiki/Key:mountain_pass
    # See https://www.openstreetmap.org/node/4977980007 (Col du Galibier)
    api = overpy.Overpass()
    bounds = GpxBounds.from_list(list_lon=gpx.list_lon,
                                 list_lat=gpx.list_lat).add_relative_margin(0.1)
    bounds_str = f"({bounds.lat_min:.2f}, {bounds.lon_min:.2f}, {bounds.lat_max:.2f}, {bounds.lon_max:.2f})"
    result = api.query(f"""(
        // Query for mountain passes and saddles
        nwr["natural"="saddle"]{bounds_str};
        nwr["mountain_pass"="yes"]{bounds_str};

        // Query for hiking cols
        nwr["hiking"="yes"]["tourism"="information"]{bounds_str};
        nwr["hiking"="yes"]["information"="guidepost"]{bounds_str};
    );
    out body;""")

    ids: list[int] = []
    passes: list[MountainPass] = []
    for node in result.nodes:
        lon, lat = float(node.lon), float(node.lat)
        tags = node.tags

        if "name" in tags and "ele" in tags:
            name, ele = str(node.tags["name"]), float(node.tags["ele"])

            if "hiking" in tags and tags["hiking"] == "yes":
                if "col " not in name.lower():
                    continue

            # Check if close to the GPX track
            lat_lon_np = np.array((lat, lon))
            distances = np.linalg.norm(gpx_curve - lat_lon_np, axis=-1)
            closest_idx = int(np.argmin(distances))
            closest_distance = distances[closest_idx]
            if closest_distance > max_dist_deg:
                continue

            # Check if the mountain pass is not already in the list
            if len(passes) != 0:
                distances = np.linalg.norm(np.array([[m.lat, m.lon] for m in passes]) - lat_lon_np, axis=-1)
                if np.min(distances) < local_m_to_deg(200):
                    continue

            ids.append(closest_idx)
            passes.append(MountainPass(ele=ele, name=name, lon=lon, lat=lat))

    return ids, passes


def is_close_to_a_mountain_pass(lon: float, lat: float,
                                mountain_passes: list[MountainPass],
                                max_dist_m: float) -> bool:
    """aaaaaaaa"""
    if len(mountain_passes) == 0:
        return False
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
