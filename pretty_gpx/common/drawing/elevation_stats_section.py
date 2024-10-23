#!/usr/bin/python3
"""Stats Section with Elevation Profile."""
import math

import numpy as np
from scipy.interpolate import interp1d
from scipy.ndimage import uniform_filter1d

from pretty_gpx.common.drawing.base_drawing_figure import BaseDrawingFigure
from pretty_gpx.common.drawing.drawing_data import PolyFillData
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.layout.elevation_vertical_layout import ElevationVerticalLayout


def downsample(x: np.ndarray, y: np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Downsample the signla Y evaluate at X to N points, applying a simple moving average smoothing beforehand."""
    if len(x) <= n:
        assert len(x) == len(y)
        return x, y 
    smoothed_y = uniform_filter1d(y, size=len(x) // n, mode="nearest")
    interpolator = interp1d(x, smoothed_y, kind='linear')

    resampled_x = np.linspace(np.min(x), np.max(x), n, endpoint=True)
    resampled_y = interpolator(resampled_x)

    return resampled_x, resampled_y


class ElevationStatsSection:
    """Generate the polygon of the stats section with the elevation profile above."""

    def __init__(self,
                 layout: ElevationVerticalLayout,
                 paper_fig: BaseDrawingFigure,
                 track: GpxTrack,
                 pts_per_mm: float = 2.0) -> None:
        b = paper_fig.gpx_bounds

        y_lat_up = b.lat_min + b.dlat * (layout.stats_relative_h + layout.elevation_relative_h)
        y_lat_bot = b.lat_min + b.dlat * layout.stats_relative_h

        normalized_x_lon = np.array(track.list_cumul_dist_km)/track.list_cumul_dist_km[-1]
        self.__elevation_poly_x_lon = b.lon_min + b.dlon*normalized_x_lon

        ele = np.array(track.list_ele_m)
        ele_min, ele_max = np.min(ele), np.max(ele)
        self.__elevation_poly_y_lat = y_lat_bot + (y_lat_up-y_lat_bot) * (ele-ele_min) / (ele_max-ele_min)

        downsampled_x, downsampled_y = downsample(x=self.__elevation_poly_x_lon,
                                                  y=self.__elevation_poly_y_lat,
                                                  n=math.ceil(paper_fig.paper_size.w_mm * pts_per_mm))

        # Complete the polygon for the elevation profile
        self.fill_poly = PolyFillData(x=[b.lon_min, b.lon_min] + downsampled_x.tolist() + [b.lon_max, b.lon_max],
                                      y=[b.lat_min, y_lat_bot] + downsampled_y.tolist() + [y_lat_bot, b.lat_min])

        self.section_center_lat_y = 0.5 * (y_lat_bot + b.lat_min)
        self.section_center_lon_x = b.lon_center

    def get_profile_lat_y(self, k: int) -> float:
        """Get the latitude of the elevation profile on the poster at index k in the original GPX track."""
        return self.__elevation_poly_y_lat[k]

    def get_profile_lon_x(self, k: int) -> float:
        """Get the longitude of the elevation profile on the poster at index k in the original GPX track."""
        return self.__elevation_poly_x_lon[k]
