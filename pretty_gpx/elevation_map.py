#!/usr/bin/python3
"""Elevation Map."""

import os
from dataclasses import dataclass
from typing import List
from typing import Tuple

import cv2
import numpy as np
import rasterio
from dem_stitcher import stitch_dem
from gpx_bounds import GpxBounds


@dataclass
class ElevationMap:
    elevation: np.ndarray
    bounds: GpxBounds

    @staticmethod
    def download(bounds: GpxBounds, cache_folder: str) -> 'ElevationMap':
        """aaaa"""
        bounds = bounds.round(n_decimals=2)  # Round to use as hash
        cache_basename = f"dem_{bounds.lat_min:.2f}_{bounds.lon_min:.2f}_{bounds.lat_max:.2f}_{bounds.lon_max:.2f}.tif"
        cache_tif = os.path.join(cache_folder, cache_basename)

        if not os.path.isfile(cache_tif):
            os.makedirs(cache_folder, exist_ok=True)
            elevation, p = stitch_dem([bounds.lon_min, bounds.lat_min, bounds.lon_max, bounds.lat_max],
                                      dem_name='glo_30',  # Global Copernicus 30 meter resolution DEM
                                      dst_ellipsoidal_height=False,
                                      dst_area_or_point='Point')
            with rasterio.open(cache_tif, 'w', **p) as f:
                f.write(elevation, 1)
                f.update_tags(AREA_OR_POINT='Point')

        elevation = rasterio.open(cache_tif).read()[0]

        return ElevationMap(elevation=elevation, bounds=bounds)

    def rescale(self, scale: float) -> 'ElevationMap':
        """aaaaaa"""
        new_h = int(scale*self.elevation.shape[0])
        new_w = int(scale*self.elevation.shape[1])
        new_elevation = cv2.resize(self.elevation, (new_w, new_h),
                                   interpolation=cv2.INTER_LANCZOS4)  # bicubic is ugly

        # FIXME fix aliasing when upsapling

        return ElevationMap(elevation=new_elevation, bounds=self.bounds)

    def project_on_image(self, list_lon: List[float], list_lat: List[float]) -> Tuple[List[float], List[float]]:
        """lon, lat to XY"""
        x_pix = [(lon - self.bounds.lon_min) / (self.bounds.lon_max-self.bounds.lon_min) * self.elevation.shape[1]
                 for lon in list_lon]
        y_pix = [(self.bounds.lat_max - lat) / (self.bounds.lat_max-self.bounds.lat_min) * self.elevation.shape[0]
                 for lat in list_lat]
        return x_pix, y_pix
