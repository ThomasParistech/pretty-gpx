#!/usr/bin/python3
"""Gpx Track."""
from dataclasses import dataclass
from dataclasses import field

import matplotlib.pyplot as plt
import numpy as np
from gpxpy.gpx import GPXTrackPoint

from pretty_gpx.common.gpx.gpx_io import load_gpxpy
from pretty_gpx.common.utils.asserts import assert_close
from pretty_gpx.common.utils.asserts import assert_not_empty
from pretty_gpx.common.utils.asserts import assert_same_len
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.utils import safe

DEBUG_TRACK = False


def local_m_to_deg(m: float) -> float:
    """Convert meters to degrees that the earth is locally planar."""
    return m * 180. / (np.pi * 6371*1e3)


@dataclass
class GpxTrack:
    """GPX Track."""
    list_lon: list[float] = field(default_factory=list)
    list_lat: list[float] = field(default_factory=list)
    list_ele_m: list[float] = field(default_factory=list)
    list_cumul_dist_km: list[float] = field(default_factory=list)

    uphill_m: float = 0.0

    def __post_init__(self):
        assert_same_len((self.list_lon, self.list_lat, self.list_ele_m, self.list_cumul_dist_km))

    @staticmethod
    def load(gpx_path: str | bytes) -> 'GpxTrack':
        """Load GPX file and return GpxTrack along with total distance (in km) and d+ (in m)."""
        gpx = load_gpxpy(gpx_path)

        gpx_track = GpxTrack()
        for track in gpx.tracks:
            for segment in track.segments:
                append_track_to_gpx_track(gpx_track, segment.points)

        if len(gpx_track.list_lon) == 0:
            raise ValueError("No track found in GPX file (or elevation is missing)")

        if DEBUG_TRACK:
            plt.plot(gpx_track.list_lon, gpx_track.list_lat)
            plt.xlabel('Longitude (in °)')
            plt.ylabel('Latitude (in °)')
            plt.figure()
            plt.plot(gpx_track.list_ele_m)
            plt.ylabel('Elevation (in m)')
            plt.show()

        assert_close(gpx_track.list_cumul_dist_km[-1], gpx.length_3d()*1e-3, eps=1e-3,
                     msg="Total distance must be coherent with `gpx.length_3d()` from gpxpy")

        gpx_track.uphill_m = gpx.get_uphill_downhill().uphill

        logger.info(f"Loaded GPX track with {len(gpx_track.list_lon)} points: "
                    f"Distance={gpx_track.list_cumul_dist_km[-1]:.1f}km and uphill={gpx_track.uphill_m:.0f}m")

        return gpx_track

    def is_closed(self, dist_m: float) -> bool:
        """Estimate if the track is closed."""
        dist_deg = float(np.linalg.norm((self.list_lon[0] - self.list_lon[-1],
                                         self.list_lat[0] - self.list_lat[-1])))
        return dist_deg < local_m_to_deg(dist_m)

    @staticmethod
    def merge(list_gpx_track: list['GpxTrack']) -> 'GpxTrack':
        """Merge multiple GpxTrack into one."""
        assert_not_empty(list_gpx_track)

        list_cumul_d = list_gpx_track[0].list_cumul_dist_km
        for gpx in list_gpx_track[1:]:
            list_cumul_d.extend([cumul_d + list_cumul_d[-1] for cumul_d in gpx.list_cumul_dist_km])

        return GpxTrack(list_lon=[lon
                                  for gpx in list_gpx_track
                                  for lon in gpx.list_lon],
                        list_lat=[lat
                                  for gpx in list_gpx_track
                                  for lat in gpx.list_lat],
                        list_ele_m=[ele
                                    for gpx in list_gpx_track
                                    for ele in gpx.list_ele_m],
                        list_cumul_dist_km=list_cumul_d,
                        uphill_m=sum(gpx.uphill_m for gpx in list_gpx_track))


def append_track_to_gpx_track(gpx_track: GpxTrack, track_points: list[GPXTrackPoint]) -> None:
    """"Append track points to a GpxTrack. Update cumulative distance like in gpxpy with GPX.length_3d()."""
    has_started = len(gpx_track.list_lon) > 0

    if has_started:
        prev_cumul_dist_km = gpx_track.list_cumul_dist_km[-1]
    else:
        prev_cumul_dist_km = 0.0

    prev_point: GPXTrackPoint | None = None
    for point in track_points:
        if point.elevation is None:
            if not has_started:
                continue  # Skip first point if no elevation
            point.elevation = gpx_track.list_ele_m[-1]

        gpx_track.list_lon.append(point.longitude)
        gpx_track.list_lat.append(point.latitude)
        gpx_track.list_ele_m.append(point.elevation)

        if prev_point is not None:
            prev_cumul_dist_km += safe(prev_point.distance_3d(point)) * 1e-3

        gpx_track.list_cumul_dist_km.append(prev_cumul_dist_km)

        prev_point = point
