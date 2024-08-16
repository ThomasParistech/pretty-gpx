#!/usr/bin/python3
"""Map Data."""
import math
from dataclasses import dataclass

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
class MountainHut:
    """Mountain Hut Data."""
    name: str | None
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

    huts: list[MountainHut]
    hut_ids: list[int]
    daily_dist_km: list[float]  # Distance (in km) of each daily track

    @staticmethod
    def from_path(list_gpx_path: list[str] | list[bytes],
                  strict_ths_m: float = 50,
                  loose_ths_m: float = 1000) -> 'AugmentedGpxData':
        """aaaaa ordered gpx list"""
        (gpx_track,
         dist_km,
         uphill_m,
         daily_dist_km,
         huts_ids, huts_names) = find_huts_between_daily_tracks(list_gpx_path)

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
                                daily_dist_km=daily_dist_km,
                                start_name=start_name,
                                end_name=end_name,
                                is_closed=is_closed,
                                mountain_passes=mountain_passes,
                                passes_ids=passes_ids,
                                huts=huts_names,
                                hut_ids=huts_ids)


def overpass_request(query_elements: list[str], gpx_track: GpxTrack) -> overpy.Result:
    """aaaaa"""
    # See https://wiki.openstreetmap.org/wiki/Key:natural
    # See https://wiki.openstreetmap.org/wiki/Key:mountain_pass
    # See https://wiki.openstreetmap.org/wiki/Tag:tourism=alpine_hut
    api = overpy.Overpass()
    bounds = GpxBounds.from_list(list_lon=gpx_track.list_lon,
                                 list_lat=gpx_track.list_lat).add_relative_margin(0.1)
    bounds_str = f"({bounds.lat_min:.5f}, {bounds.lon_min:.5f}, {bounds.lat_max:.5f}, {bounds.lon_max:.5f})"

    query_body = "\n".join([f"{element}{bounds_str};" for element in query_elements])
    result = api.query(f"""(
       {query_body}
    );
    out body;""")
    return result


def get_close_mountain_passes(gpx: GpxTrack, max_dist_m: float) -> tuple[list[int], list[MountainPass]]:
    """Get mountain passes close to a GPX track."""
    max_dist_deg = local_m_to_deg(max_dist_m)
    gpx_curve = np.stack((gpx.list_lat, gpx.list_lon), axis=-1)

    result = overpass_request(["nwr['natural'='saddle']",
                               "nwr['natural'='peak']",
                               "nwr['mountain_pass'='yes']",
                               "nwr['hiking'='yes']['tourism'='information']",
                               "nwr['hiking'='yes']['information'='guidepost']"],
                              gpx)

    # See https://www.openstreetmap.org/node/4977980007 (Col du Galibier)
    # See https://www.openstreetmap.org/node/12068789882 (Col de la Vanoise)
    # See https://www.openstreetmap.org/node/34975894 (Pic du Cabaliros)
    ids: list[int] = []
    passes: list[MountainPass] = []
    for node in result.nodes:
        tags = node.tags

        if "name" in tags and "ele" in tags:
            if not node.tags["ele"].isnumeric():
                continue
            name = str(node.tags["name"])
            ele = float(node.tags["ele"])

            if "hiking" in tags and tags["hiking"] == "yes":
                if "col " not in name.lower():
                    continue

            # Check if close to the GPX track
            lon, lat = float(node.lon), float(node.lat)
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


def find_huts_between_daily_tracks(list_gpx_path: list[str] | list[bytes],
                                   max_dist_m: float = 300) -> tuple[GpxTrack,
                                                                     float,
                                                                     float,
                                                                     list[float],
                                                                     list[int],
                                                                     list[MountainHut]]:
    """Merge ordered GPX tracks into a single one and find huts between them."""
    # Load GPX tracks
    list_gpx_track: list[GpxTrack] = []
    list_dist_km: list[float] = []
    list_uphill_m: list[float] = []
    for path in list_gpx_path:
        gpx_track, dist_km, uphill_m = GpxTrack.load(path)
        list_gpx_track.append(gpx_track)
        list_dist_km.append(dist_km)
        list_uphill_m.append(uphill_m)

    if len(list_gpx_track) == 1:
        return list_gpx_track[0], list_dist_km[0], list_uphill_m[0], list_dist_km, [], []

    # Assert consecutive tracks
    consecutive_ths_deg = local_m_to_deg(1000)
    for i in range(len(list_gpx_track) - 1):
        crt_track = list_gpx_track[i]
        next_track = list_gpx_track[i+1]

        distance = np.linalg.norm((crt_track.list_lon[-1] - next_track.list_lon[0],
                                   crt_track.list_lat[-1] - next_track.list_lat[0]))
        assert distance < consecutive_ths_deg, "GPX tracks are not consecutive"

    # Merge GPX tracks
    full_dist_km = sum(list_dist_km)
    full_uphill_m = sum(list_uphill_m)
    full_gpx_track = GpxTrack(list_lon=[lon
                                        for gpx in list_gpx_track
                                        for lon in gpx.list_lon],
                              list_lat=[lat
                                        for gpx in list_gpx_track
                                        for lat in gpx.list_lat],
                              list_ele=[ele
                                        for gpx in list_gpx_track
                                        for ele in gpx.list_ele])

    # Request the huts
    result = overpass_request(["nwr['tourism'='alpine_hut']",
                               "nwr['tourism'='wilderness_hut']",
                               "nwr['tourism'='camp_site']"],
                              full_gpx_track)

    # See https://www.openstreetmap.org/way/112147855 (Refuge Plan-Sec)
    # See https://www.openstreetmap.org/node/451703419 (Refuge des Barmettes)
    candidate_huts: list[MountainHut] = []
    for node in result.nodes:
        lon, lat = float(node.lon), float(node.lat)
        if "name" in node.tags:
            name = str(node.tags["name"])
            candidate_huts.append(MountainHut(name=name, lon=lon, lat=lat))

    for way in result.ways:
        if "name" in way.tags:
            name = str(way.tags["name"])
            nodes = way.get_nodes(resolve_missing=True)
            avg_lat = float(np.mean([float(node.lat) for node in nodes]))
            avg_lon = float(np.mean([float(node.lon) for node in nodes]))
            candidate_huts.append(MountainHut(name=name, lon=avg_lon, lat=avg_lat))

    # Estimate the huts locations
    max_dist_deg = local_m_to_deg(max_dist_m)
    huts_ids = np.cumsum([len(gpx.list_lon) for gpx in list_gpx_track[:-1]]).tolist()

    huts: list[MountainHut] = []
    candidates_lat_lon_np = np.array([[h.lat, h.lon] for h in candidate_huts])
    for hut_id in huts_ids:
        hut_lat, hut_lon = full_gpx_track.list_lat[hut_id], full_gpx_track.list_lon[hut_id]

        distances = np.linalg.norm(candidates_lat_lon_np - np.array((hut_lat, hut_lon)), axis=-1)
        closest_idx = int(np.argmin(distances))
        closest_distance = distances[closest_idx]
        if closest_distance < max_dist_deg:
            huts.append(candidate_huts[closest_idx])
        else:
            huts.append(MountainHut(name=None, lat=hut_lat, lon=hut_lon))

    print(f"Huts: {', '.join([h.name if h.name is not None else '?' for h in huts if h.name])}")
    return full_gpx_track, full_dist_km, full_uphill_m, list_dist_km, huts_ids, huts
