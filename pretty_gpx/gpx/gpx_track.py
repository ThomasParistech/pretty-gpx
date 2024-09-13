#!/usr/bin/python3
"""Gpx Track."""
from dataclasses import dataclass

import gpxpy
import gpxpy.gpx
import matplotlib.pyplot as plt
import numpy as np
from gpxpy.gpx import GPXTrackPoint

from pretty_gpx.gpx.gpx_bounds import GpxBounds
from pretty_gpx.gpx.gpx_io import load_gpxpy
from pretty_gpx.utils.logger import logger

DEBUG_TRACK = False


def local_m_to_deg(m: float) -> float:
    """Convert meters to degrees that the earth is locally planar."""
    return m * 180. / (np.pi * 6371*1e3)


@dataclass
class GpxTrack:
    """GPX Track."""
    list_lon: list[float]
    list_lat: list[float]
    list_ele: list[float]
    list_cumul_d: list[float]
    list_cumul_ele: list[float]

    @staticmethod
    def load(gpx_path: str | bytes) -> 'GpxTrack':  # noqa: PLR0915
        """Load GPX file and return GpxTrack along with total distance (in km) and d+ (in m)."""
        gpx = load_gpxpy(gpx_path)

        gpx_track = GpxTrack([], [], [], [], [])

        all_segment_cumul_d = 0.
        all_segment_cumul_ele = 0.

        point_prev: GPXTrackPoint | None = None
        n_skips = 0
        for track in gpx.tracks:
            for segment in track.segments:
                for idx, point in enumerate(segment.points):
                    assert isinstance(point, GPXTrackPoint)
                    if point.elevation is None:
                        if len(gpx_track.list_ele) == 0:
                            n_skips += 1
                            continue  # Skip first point if no elevation
                        point.elevation = gpx_track.list_ele[-1]

                    gpx_track.list_lon.append(point.longitude)
                    gpx_track.list_lat.append(point.latitude)
                    gpx_track.list_ele.append(point.elevation)
                    if idx == 0:
                        d = all_segment_cumul_d
                        previous_cum_d = all_segment_cumul_d
                        h_diff = all_segment_cumul_ele
                        previous_cum_ele = all_segment_cumul_ele
                    else:
                        assert point_prev is not None
                        d = gpxpy.geo.distance(point_prev.latitude,
                                               point_prev.longitude,
                                               point_prev.elevation,
                                               point.latitude,
                                               point.longitude,
                                               point.elevation)*1e-3
                        h_diff = point.elevation - point_prev.elevation  # type: ignore
                        if h_diff < 0:
                            h_diff = 0.0

                    previous_cum_d += d
                    previous_cum_ele += h_diff

                    gpx_track.list_cumul_d.append(previous_cum_d)
                    gpx_track.list_cumul_ele.append(previous_cum_ele)

                    point_prev = point

                all_segment_cumul_d += previous_cum_d
                all_segment_cumul_ele += previous_cum_ele

        if len(gpx_track.list_lon) == 0:
            if n_skips > 0:
                raise ValueError(f"No elevation found in GPX file (Skipped {n_skips} points)")
            raise ValueError("No track found in GPX file")

        if DEBUG_TRACK:
            plt.plot(gpx_track.list_lon, gpx_track.list_lat)
            plt.xlabel('Longitude (in °)')
            plt.ylabel('Latitude (in °)')
            plt.figure()
            plt.plot(gpx_track.list_ele)
            plt.ylabel('Elevation (in m)')
            plt.show()

        logger.info(f"Distance\nPoint to point: {all_segment_cumul_d}"
                    f"\tTotal file: {gpx.length_3d()*1e-3}")
        logger.info(f"Climb\nPoint to point: {all_segment_cumul_ele}",
                    f"\tAveraged on 3 points: {gpx.get_uphill_downhill().uphill}")

        # assert_close(all_segment_cumul_d, gpx.length_3d()*1e-3, eps=0.05*all_segment_cumul_d,
        #              msg="Total distance is not coherent between point to point calculation and total sum")

        # # As the climb is averaged 20% seems good, as there are more points, then it should be
        # # possible to reduce the threshold
        # assert_close(all_segment_cumul_ele, gpx.get_uphill_downhill().uphill, eps=0.2*all_segment_cumul_ele,
        #              msg="Total climb is not coherent between point to point calculation and total sum")

        # TODO: fix cumulative distance

        return gpx_track

    def is_closed(self, dist_m: float) -> bool:
        """Estimate if the track is closed."""
        dist_deg = float(np.linalg.norm((self.list_lon[0] - self.list_lon[-1],
                                         self.list_lat[0] - self.list_lat[-1])))
        return dist_deg < local_m_to_deg(dist_m)

    def project_on_image(self,
                         img: np.ndarray,
                         bounds: GpxBounds) -> tuple[list[float], list[float]]:
        """Convert lat/lon to pixel coordinates."""
        x_pix = [(lon - bounds.lon_min) / (bounds.lon_max-bounds.lon_min) * img.shape[1]
                 for lon in self.list_lon]
        y_pix = [(bounds.lat_max - lat) / (bounds.lat_max-bounds.lat_min) * img.shape[0]
                 for lat in self.list_lat]
        return x_pix, y_pix

    @staticmethod
    def merge(list_gpx_track: list['GpxTrack']) -> 'GpxTrack':
        """Merge multiple GpxTrack into one."""
        list_lon = [lon
                    for gpx in list_gpx_track
                    for lon in gpx.list_lon]
        list_lat = [lat
                    for gpx in list_gpx_track
                    for lat in gpx.list_lat]
        list_ele = [ele
                    for gpx in list_gpx_track
                    for ele in gpx.list_ele]
        total_d_track = [0.]
        total_ele_track = [0.]
        for gpx in list_gpx_track:
            total_d_track.append(total_d_track[-1]+gpx.list_cumul_d[-1])
            total_ele_track.append(total_ele_track[-1]+gpx.list_cumul_ele[-1])

        list_cumul_d = [cumul_d + total_d_track[idx]
                        for idx, gpx in enumerate(list_gpx_track)
                        for cumul_d in gpx.list_cumul_d]
        list_cumul_ele = [cumul_ele + total_d_track[idx]
                          for idx, gpx in enumerate(list_gpx_track)
                          for cumul_ele in gpx.list_cumul_ele]

        return GpxTrack(list_lon=list_lon,
                        list_lat=list_lat,
                        list_ele=list_ele,
                        list_cumul_d=list_cumul_d,
                        list_cumul_ele=list_cumul_ele)
