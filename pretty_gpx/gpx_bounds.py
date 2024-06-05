#!/usr/bin/python3
"""GPX Bounds."""
from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass
class GpxBounds:
    """aaaaa"""
    lon_min: float
    lon_max: float
    lat_min: float
    lat_max: float

    @staticmethod
    def from_list(*, list_lon: List[float], list_lat: List[float]) -> 'GpxBounds':
        """aaaaaaa"""
        return GpxBounds(lon_min=np.min(list_lon),
                         lon_max=np.max(list_lon),
                         lat_min=np.min(list_lat),
                         lat_max=np.max(list_lat))

    def add_relative_margin(self, rel_margin: float) -> 'GpxBounds':
        """aaaaaa"""
        lon_margin = rel_margin * (self.lon_max - self.lon_min)
        lat_margin = rel_margin * (self.lat_max - self.lat_min)

        return GpxBounds(lon_min=self.lon_min - lon_margin,
                         lon_max=self.lon_max + lon_margin,
                         lat_min=self.lat_min - lat_margin,
                         lat_max=self.lat_max + lat_margin)

    def round(self, n_decimals: int) -> 'GpxBounds':
        """aaaaaa"""
        return GpxBounds(lon_min=round(self.lon_min, ndigits=n_decimals),
                         lon_max=round(self.lon_max, ndigits=n_decimals),
                         lat_min=round(self.lat_min, ndigits=n_decimals),
                         lat_max=round(self.lat_max, ndigits=n_decimals))
