#!/usr/bin/python3
"""Map Data."""
from dataclasses import dataclass

import numpy as np

from pretty_gpx.common.gpx.gpx_io import cast_to_list_gpx_path
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.gpx.gpx_track import local_m_to_deg
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import profile


@dataclass
class CityAugmentedGpxData:
    """Class storing the GPX track augmented with names of start/end points and mountain passes/huts along the way."""
    track: GpxTrack

    @property
    def dist_km(self) -> float:
        """Total distance in km."""
        return self.track.list_cumul_dist_km[-1]

    @property
    def uphill_m(self) -> float:
        """Total climb in m."""
        return self.track.uphill_m

    @property
    def duration_s(self) -> float | None:
        """Total duration in s."""
        return self.track.duration_s


    @profile
    @staticmethod
    def from_path(list_gpx_path: str | bytes | list[str] | list[bytes],
                  strict_ths_m: float = 50,
                  loose_ths_m: float = 1000) -> 'CityAugmentedGpxData':
        """Create an AugmentedGpxData instance from an ordered list of daily GPX files."""
        list_gpx_path = cast_to_list_gpx_path(list_gpx_path)

        gpx_track = merge_track(list_gpx_path)


        return CityAugmentedGpxData(track=gpx_track)


@profile
def merge_track(list_gpx_path: list[str] | list[bytes],
                max_dist_m: float = 1000) -> GpxTrack:
    """Merge ordered GPX tracks into a single one."""
    # Load GPX tracks
    list_gpx_track = [GpxTrack.load(path) for path in list_gpx_path]

    if len(list_gpx_track) == 1:
        return list_gpx_track[0]

    # Assert consecutive tracks
    for i in range(len(list_gpx_track) - 1):
        crt_track = list_gpx_track[i]
        next_track = list_gpx_track[i+1]

        distance = np.linalg.norm((crt_track.list_lon[-1] - next_track.list_lon[0],
                                   crt_track.list_lat[-1] - next_track.list_lat[0]))
        if distance > local_m_to_deg(max_dist_m):  # 5km Tolerance
            raise AssertionError("Too large gap between consecutive GPX tracks. "
                                 "Check the alphabetical order of the files. "
                                 "Or edit the GPX files.")

        if distance > local_m_to_deg(max_dist_m/2.0):
            logger.warning("Warning: GPX tracks are not perfectly consecutive")

    # Merge GPX tracks
    full_gpx_track = GpxTrack.merge(list_gpx_track=list_gpx_track)
    return full_gpx_track