#!/usr/bin/python3
"""GPX Bounds."""
from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np

from pretty_gpx.common.gpx.gpx_distance import get_delta_xy
from pretty_gpx.common.gpx.gpx_distance import latlon_aspect_ratio


@dataclass
class GpxBounds:
    """GPX Bounds in Latitude/Longitude."""
    lon_min: float
    lon_max: float
    lat_min: float
    lat_max: float

    def __str__(self) -> str:
        """Return a string representation of GpxBounds."""
        return f"Lon [{self.lon_min:.2f}, {self.lon_max:.2f}] and Lat [{self.lat_min:.2f},{self.lat_max:.2f}]"

    @staticmethod
    def union(list_bounds: Iterable['GpxBounds']) -> 'GpxBounds':
        """Union of a list of bounds."""
        return GpxBounds(lon_min=min([b.lon_min for b in list_bounds]),
                         lon_max=max([b.lon_max for b in list_bounds]),
                         lat_min=min([b.lat_min for b in list_bounds]),
                         lat_max=max([b.lat_max for b in list_bounds]))

    @staticmethod
    def from_list(*, list_lon: list[float], list_lat: list[float]) -> 'GpxBounds':
        """Init GpxBounds from list of latitudes and longitudes."""
        return GpxBounds(lon_min=np.min(list_lon),
                         lon_max=np.max(list_lon),
                         lat_min=np.min(list_lat),
                         lat_max=np.max(list_lat))

    @staticmethod
    def from_center(*, lon_center: float, lat_center: float, dlon: float, dlat: float) -> 'GpxBounds':
        """Init GpxBounds from center and span."""
        return GpxBounds(lon_min=lon_center - 0.5*dlon,
                         lon_max=lon_center + 0.5*dlon,
                         lat_min=lat_center - 0.5*dlat,
                         lat_max=lat_center + 0.5*dlat)

    def add_relative_margin(self, rel_margin: float) -> 'GpxBounds':
        """Add a relative margin to the bounds."""
        return GpxBounds.from_center(lon_center=self.lon_center,
                                     lat_center=self.lat_center,
                                     dlon=self.dlon*(1. + rel_margin),
                                     dlat=self.dlat*(1. + rel_margin))

    def is_in_bounds(self, lon: float, lat: float) -> bool:
        """Returns if a point is in the bounds or not."""
        return self.lat_min < lat and lat < self.lat_max and self.lon_min < lon and lon < self.lon_max

    @property
    def lon_center(self) -> float:
        """Longitude center."""
        return 0.5 * (self.lon_min + self.lon_max)

    @property
    def lat_center(self) -> float:
        """Latitude center."""
        return 0.5 * (self.lat_min + self.lat_max)

    @property
    def dlon(self) -> float:
        """Longitude span."""
        return self.lon_max - self.lon_min

    @property
    def dlat(self) -> float:
        """Latitude span."""
        return self.lat_max - self.lat_min

    @property
    def latlon_aspect_ratio(self) -> float:
        """Aspect ratio of the lat/lon map."""
        return latlon_aspect_ratio(lat=self.lat_center)

    @property
    def dx_dy_m(self) -> tuple[float, float]:
        """Delta x and delta y."""
        diff_xy = np.abs(get_delta_xy(lonlat_1=np.array((self.lon_max, self.lon_max)),
                                      lonlat_2=np.array((self.lon_min, self.lon_min))))
        return float(diff_xy[0]), float(diff_xy[1])

    @property
    def area_m2(self) -> float:
        """The area of the bounds in meters squared."""
        dx, dy = self.dx_dy_m
        return dx * dy

    @property
    def diagonal_m(self) -> float:
        """The diagonal of the bounds in meters."""
        return float(np.linalg.norm(self.dx_dy_m))
