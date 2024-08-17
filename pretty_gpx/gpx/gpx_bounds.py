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

    def add_relative_margin(self, rel_margin: float) -> 'GpxBounds':
        """Add a relative margin to the bounds."""
        lon_margin = rel_margin * (self.lon_max - self.lon_min)
        lat_margin = rel_margin * (self.lat_max - self.lat_min)

        return GpxBounds(lon_min=self.lon_min - lon_margin,
                         lon_max=self.lon_max + lon_margin,
                         lat_min=self.lat_min - lat_margin,
                         lat_max=self.lat_max + lat_margin)

    def round(self, n_decimals: int) -> 'GpxBounds':
        """Round the bounds to n decimals."""
        return GpxBounds(lon_min=round(self.lon_min, ndigits=n_decimals),
                         lon_max=round(self.lon_max, ndigits=n_decimals),
                         lat_min=round(self.lat_min, ndigits=n_decimals),
                         lat_max=round(self.lat_max, ndigits=n_decimals))
