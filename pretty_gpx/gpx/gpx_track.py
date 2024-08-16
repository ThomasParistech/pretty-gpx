#!/usr/bin/python3
"""Gpx Track."""
import matplotlib.pyplot as plt
from dataclasses import dataclass

import gpxpy
import gpxpy.gpx
import numpy as np

from pretty_gpx.gpx.gpx_bounds import GpxBounds
from pretty_gpx.utils import assert_isfile


DEBUG_TRACK = False


def local_m_to_deg(m: float) -> float:
    """aaaa"""
    return m * 180. / (np.pi * 6371*1e3)


@dataclass
class GpxTrack:
    """aaaaaaaa"""
    list_lon: list[float]
    list_lat: list[float]
    list_ele: list[float]

    @staticmethod
    def load(gpx_path: str | bytes) -> tuple['GpxTrack', float, float]:
        """aaaaaa, with totl disance (in km) and d+ (in m)"""
        if isinstance(gpx_path, str):
            assert_isfile(gpx_path, ext='.gpx')
            gpx_path = open(gpx_path)
        gpx = gpxpy.parse(gpx_path)

        gpx_track = GpxTrack([], [], [])

        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if point.elevation is None:
                        if len(gpx_track.list_ele) == 0:
                            continue  # Skip first point if no elevation
                        point.elevation = gpx_track.list_ele[-1]

                    gpx_track.list_lon.append(point.longitude)
                    gpx_track.list_lat.append(point.latitude)
                    gpx_track.list_ele.append(point.elevation)

        if DEBUG_TRACK:
            plt.plot(gpx_track.list_lon, gpx_track.list_lat)
            plt.xlabel('Longitude (in °)')
            plt.ylabel('Latitude (in °)')
            plt.figure()
            plt.plot(gpx_track.list_ele)
            plt.ylabel('Elevation (in m)')
            plt.show()

        return gpx_track, gpx.length_3d()*1e-3, gpx.get_uphill_downhill().uphill

    def is_closed(self, dist_m: float) -> bool:
        """aaaa"""
        dist_deg = float(np.linalg.norm((self.list_lon[0] - self.list_lon[-1],
                                         self.list_lat[0] - self.list_lat[-1])))
        return dist_deg < local_m_to_deg(dist_m)

    def project_on_image(self,
                         img: np.ndarray,
                         bounds: GpxBounds) -> tuple[list[float], list[float]]:
        """lon, lat to XY"""
        x_pix = [(lon - bounds.lon_min) / (bounds.lon_max-bounds.lon_min) * img.shape[1]
                 for lon in self.list_lon]
        y_pix = [(bounds.lat_max - lat) / (bounds.lat_max-bounds.lat_min) * img.shape[0]
                 for lat in self.list_lat]
        return x_pix, y_pix
