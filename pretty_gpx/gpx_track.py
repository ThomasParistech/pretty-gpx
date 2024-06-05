#!/usr/bin/python3
"""Gpx Track."""
from dataclasses import dataclass
from typing import BinaryIO
from typing import List
from typing import TextIO
from typing import Tuple
from typing import Union

import gpxpy
import gpxpy.gpx
import numpy as np


def local_m_to_deg(m: float) -> float:
    """aaaa"""
    return m * 180. / (np.pi * 6371*1e3)


@dataclass
class GpxTrack:
    """aaaaaaaa"""
    list_lon: List[float]
    list_lat: List[float]
    list_ele: List[float]

    @staticmethod
    def load(gpx_path: Union[str, BinaryIO, TextIO]) -> Tuple['GpxTrack', float, float]:
        """aaaaaa, with totl disance (in km) and d+ (in m)"""
        if isinstance(gpx_path, str):
            gpx_path = open(gpx_path)
        gpx = gpxpy.parse(gpx_path)

        gpx_track = GpxTrack([], [], [])

        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    gpx_track.list_lon.append(point.longitude)
                    gpx_track.list_lat.append(point.latitude)
                    gpx_track.list_ele.append(point.elevation)

        return gpx_track, gpx.length_3d()*1e-3, gpx.get_uphill_downhill().uphill

    def is_closed(self, dist_m: float) -> bool:
        """aaaa"""
        dist_deg = float(np.linalg.norm((self.list_lon[0] - self.list_lon[-1],
                                         self.list_lat[0] - self.list_lat[-1])))
        return dist_deg < local_m_to_deg(dist_m)
