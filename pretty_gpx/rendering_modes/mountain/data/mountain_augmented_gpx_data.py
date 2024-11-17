#!/usr/bin/python3
"""Mountain Augmented GPX Data."""
import math
from dataclasses import dataclass
from typing import Final

import numpy as np

from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.data.place_name import get_place_name
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_distance import get_distance_m
from pretty_gpx.common.gpx.gpx_io import cast_to_list_gpx_path
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.structure import AugmentedGpxData
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.rendering_modes.mountain.data.mountain_huts import MountainHut
from pretty_gpx.rendering_modes.mountain.data.mountain_huts import prepare_download_mountain_huts
from pretty_gpx.rendering_modes.mountain.data.mountain_huts import process_mountain_huts
from pretty_gpx.rendering_modes.mountain.data.mountain_passes import MountainPass
from pretty_gpx.rendering_modes.mountain.data.mountain_passes import prepare_download_mountain_passes
from pretty_gpx.rendering_modes.mountain.data.mountain_passes import process_mountain_passes

STRICT_THS_M: Final[float] = 50
LOOSE_THS_M: Final[float] = 1000


class GpxBoundsTooLargeError(Exception):
    """Raised when the GPX area is too large to download elevation map."""


@dataclass
class MountainAugmentedGpxData(AugmentedGpxData):
    """Class storing the GPX track augmented with names of start/end points and mountain passes/huts along the way."""
    start_name: str | None
    end_name: str | None

    is_closed: bool

    mountain_passes: list[MountainPass]
    passes_ids: list[int]

    huts: list[MountainHut]
    hut_ids: list[int]

    @property
    def dist_km(self) -> float:
        """Total distance in km."""
        return self.track.list_cumul_dist_km[-1]

    @property
    def uphill_m(self) -> float:
        """Total climb in m."""
        return self.track.uphill_m

    @profile
    @staticmethod
    def from_paths(list_gpx_path: str | bytes | list[str] | list[bytes]) -> 'MountainAugmentedGpxData':
        """Create an AugmentedGpxData instance from an ordered list of daily GPX files."""
        list_gpx_path = cast_to_list_gpx_path(list_gpx_path)

        gpx_track, huts_ids = load_and_merge_tracks(list_gpx_path)

        bounds = gpx_track.get_bounds()
        area_squared_side_km = np.sqrt(bounds.area_m2)*1e-3

        if area_squared_side_km > 100:
            raise GpxBoundsTooLargeError(
                f"GPX area is too large to download elevation map. "
                f"Got an area equivalent to a square of {math.ceil(area_squared_side_km)}km side.")

        # OSM query
        total_query = OverpassQuery()
        prepare_download_mountain_passes(total_query, bounds)
        if len(huts_ids) != 0:
            prepare_download_mountain_huts(total_query, bounds)
        total_query.launch_queries()

        huts_names = find_huts_between_daily_tracks(gpx_track, huts_ids, total_query, bounds)

        is_closed = gpx_track.is_closed(LOOSE_THS_M)
        passes_ids, mountain_passes = get_close_mountain_passes(gpx_track, STRICT_THS_M, total_query, bounds)
        close_to_start = is_close_to_a_mountain_pass(lon=gpx_track.list_lon[0],
                                                     lat=gpx_track.list_lat[0],
                                                     mountain_passes=mountain_passes,
                                                     max_dist_m=LOOSE_THS_M)
        close_to_end = is_close_to_a_mountain_pass(lon=gpx_track.list_lon[-1],
                                                   lat=gpx_track.list_lat[-1],
                                                   mountain_passes=mountain_passes,
                                                   max_dist_m=LOOSE_THS_M)

        if close_to_start:
            start_name = None
        else:
            start_name = get_place_name(lon=gpx_track.list_lon[0], lat=gpx_track.list_lat[0])

        if close_to_end or is_closed:
            end_name = None
        else:
            end_name = get_place_name(lon=gpx_track.list_lon[-1], lat=gpx_track.list_lat[-1])

        return MountainAugmentedGpxData(track=gpx_track,
                                        start_name=start_name,
                                        end_name=end_name,
                                        is_closed=is_closed,
                                        mountain_passes=mountain_passes,
                                        passes_ids=passes_ids,
                                        huts=huts_names,
                                        hut_ids=huts_ids)


@profile
def get_close_mountain_passes(gpx: GpxTrack,
                              max_dist_m: float,
                              query: OverpassQuery,
                              bounds: GpxBounds) -> tuple[list[int], list[MountainPass]]:
    """Get mountain passes close to a GPX track."""
    gpx_lonlat = np.stack((gpx.list_lon, gpx.list_lat), axis=-1)

    candidate_passes = process_mountain_passes(query, bounds)

    ids: list[int] = []
    passes: list[MountainPass] = []
    for mpass in candidate_passes:
        # Check if close to the GPX track
        # TODO (upgrade): Use get_distances_to_track_m?
        distances_m = get_distance_m(lonlat_1=(mpass.lon, mpass.lat), lonlat_2=gpx_lonlat)
        closest_idx = int(np.argmin(distances_m))
        closest_distance_m = distances_m[closest_idx]

        if closest_distance_m > max_dist_m:
            continue

        # Check if the mountain pass is not already in the list
        if is_close_to_a_mountain_pass(mpass.lon, mpass.lat, passes, 200):
            continue

        ids.append(closest_idx)
        passes.append(mpass)

    return ids, passes


def is_close_to_a_mountain_pass(lon: float, lat: float,
                                mountain_passes: list[MountainPass],
                                max_dist_m: float) -> bool:
    """Check if a point is close to a mountain pass."""
    if len(mountain_passes) == 0:
        return False
    distances_m = get_distance_m(lonlat_1=(lon, lat), lonlat_2=np.array([[m.lon, m.lat] for m in mountain_passes]))
    return np.min(distances_m) < max_dist_m


def load_and_merge_tracks(list_gpx_path: list[str] | list[bytes]) -> tuple[GpxTrack, list[int]]:
    """Load and merge ordered GPX tracks into a single one."""
    list_gpx_track = [GpxTrack.load(path) for path in list_gpx_path]

    if len(list_gpx_track) == 1:
        return list_gpx_track[0], []

    for i in range(len(list_gpx_track) - 1):
        crt_track = list_gpx_track[i]
        next_track = list_gpx_track[i+1]

        distance_m = get_distance_m(lonlat_1=(crt_track.list_lon[-1], crt_track.list_lat[-1]),
                                    lonlat_2=(next_track.list_lon[0], next_track.list_lat[0]))

        if distance_m > 5000:  # 5km Tolerance
            raise AssertionError("Too large gap between consecutive GPX tracks. "
                                 "Check the alphabetical order of the files. "
                                 "Or edit the GPX files.")

        if distance_m > 500:
            logger.warning("Warning: GPX tracks are not perfectly consecutive")

    full_gpx_track = GpxTrack.merge(list_gpx_track=list_gpx_track)
    huts_ids = np.cumsum([len(gpx.list_lon) for gpx in list_gpx_track[:-1]]).tolist()

    return full_gpx_track, huts_ids


@profile
def find_huts_between_daily_tracks(full_gpx_track: GpxTrack,
                                   huts_ids: list[int],
                                   query: OverpassQuery,
                                   bounds: GpxBounds,
                                   max_dist_m: float = 300) -> list[MountainHut]:
    """Merge ordered GPX tracks into a single one and find huts between them."""
    if len(huts_ids) == 0:
        return []

    # Request the huts
    candidate_huts = process_mountain_huts(query, bounds)

    # Estimate the huts locations
    huts: list[MountainHut] = []
    candidates_lonlat_np = np.array([[h.lon, h.lat] for h in candidate_huts])
    for hut_id in huts_ids:
        hut_lat, hut_lon = full_gpx_track.list_lat[hut_id], full_gpx_track.list_lon[hut_id]

        distances_m = get_distance_m(lonlat_1=(hut_lon, hut_lat), lonlat_2=candidates_lonlat_np)
        closest_idx = int(np.argmin(distances_m))
        closest_distance = distances_m[closest_idx]
        if closest_distance < max_dist_m:
            huts.append(candidate_huts[closest_idx])
        else:
            name = get_place_name(lon=hut_lon, lat=hut_lat)
            # name  = None
            huts.append(MountainHut(name=name, lat=hut_lat, lon=hut_lon))

    logger.info(f"Huts: {', '.join([h.name if h.name is not None else '?' for h in huts if h.name])}")
    return huts
