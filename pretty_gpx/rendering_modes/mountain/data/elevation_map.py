#!/usr/bin/python3
"""Elevation Map."""
import os

import cv2
import numpy as np
import rasterio
from dem_stitcher import stitch_dem

from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.utils.asserts import assert_close
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import Profiling

ELEVATION_CACHE = GpxDataCacheHandler(name='elevation', extension='.tif')


def download_elevation_map(bounds: GpxBounds) -> np.ndarray:
    """Download elevation map from Copernicus DEM."""
    cache_tif = ELEVATION_CACHE.get_path(bounds)

    if os.path.isfile(cache_tif):
        logger.info(f"Load elevation map from cache for {bounds}")
    else:
        logger.info(f"Download elevation map for {bounds}")
        with Profiling.Scope("Download elevation map"):
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

    # Handle NaNs
    elevation[np.isnan(elevation)] = 0.0

    return elevation


def rescale_elevation(elevation: np.ndarray, scale: float) -> np.ndarray:
    """Upscale/Downscale elevation map."""
    new_h = int(scale*elevation.shape[0])
    new_w = int(scale*elevation.shape[1])
    new_elevation = cv2.resize(elevation, (new_w, new_h),
                               interpolation=cv2.INTER_LANCZOS4)  # bicubic is ugly

    # TODO: fix aliasing when upsapling

    return new_elevation
