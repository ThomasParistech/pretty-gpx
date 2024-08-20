#!/usr/bin/python3
"""Elevation Map."""
import hashlib
import os

import cv2
import numpy as np
import rasterio
from dem_stitcher import stitch_dem

from pretty_gpx import DEM_CACHE_DIR
from pretty_gpx.gpx.gpx_bounds import GpxBounds
from pretty_gpx.utils import assert_close


def download_elevation_map(bounds: GpxBounds) -> np.ndarray:
    """Download elevation map from Copernicus DEM."""
    bounds_str = f"{bounds.lon_min:.4f},{bounds.lon_max:.4f},{bounds.lat_min:.4f},{bounds.lat_max:.4f}"
    bounds_hash = hashlib.sha256(bounds_str.encode('utf-8')).hexdigest()

    cache_basename = f"dem_{bounds_hash}.tif"
    cache_tif = os.path.join(DEM_CACHE_DIR, cache_basename)

    if not os.path.isfile(cache_tif):
        os.makedirs(DEM_CACHE_DIR, exist_ok=True)
        elevation, p = stitch_dem([bounds.lon_min, bounds.lat_min, bounds.lon_max, bounds.lat_max],
                                  dem_name='glo_30',  # Global Copernicus 30 meter resolution DEM
                                  dst_ellipsoidal_height=False,
                                  dst_area_or_point='Point')
        with rasterio.open(cache_tif, 'w', **p) as f:
            f.write(elevation, 1)
            f.update_tags(AREA_OR_POINT='Point')

    elevation = rasterio.open(cache_tif).read()[0]
    assert_close((bounds.lat_max-bounds.lat_min)/(bounds.lon_max - bounds.lon_min),
                 elevation.shape[0]/elevation.shape[1], eps=5e-3, msg="Wrong aspect ratio for elevation map")
    return elevation


def rescale_elevation(elevation: np.ndarray, scale: float) -> np.ndarray:
    """Upscale/Downscale elevation map."""
    new_h = int(scale*elevation.shape[0])
    new_w = int(scale*elevation.shape[1])
    new_elevation = cv2.resize(elevation, (new_w, new_h),
                               interpolation=cv2.INTER_LANCZOS4)  # bicubic is ugly

    # FIXME fix aliasing when upsapling

    return new_elevation
