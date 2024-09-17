#!/usr/bin/python3
"""GPX Bounds."""
from dataclasses import dataclass

import numpy as np


@dataclass
class GpxBounds:
    """GPX Bounds in Latitude/Longitude."""
    lon_min: float
    lon_max: float
    lat_min: float
    lat_max: float

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
