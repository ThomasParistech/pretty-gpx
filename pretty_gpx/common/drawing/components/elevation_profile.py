#!/usr/bin/python3
"""Drawing Component for Elevation Profile."""
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from matplotlib.font_manager import FontProperties
from scipy.interpolate import interp1d
from scipy.ndimage import uniform_filter1d

from pretty_gpx.common.drawing.components.annotated_scatter import ScatterParams
from pretty_gpx.common.drawing.utils.drawing_figure import A4Float
from pretty_gpx.common.drawing.utils.drawing_figure import DrawingFigure
from pretty_gpx.common.drawing.utils.scatter_point import ScatterPoint
from pretty_gpx.common.drawing.utils.scatter_point import ScatterPointCategory
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_distance import get_pairwise_distance_m
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.asserts import assert_in
from pretty_gpx.common.utils.asserts import assert_same_len
from pretty_gpx.common.utils.utils import get


def downsample(x: np.ndarray, y: np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Downsample the signal Y evaluated at X to N points, applying a simple moving average smoothing beforehand."""
    assert_same_len([x, y], msg="Downsampling arrays should be the same length")
    if len(x) <= n:
        return x, y
    smoothed_y = uniform_filter1d(y, size=len(x) // n, mode="nearest")
    interpolator = interp1d(x, smoothed_y, kind='linear')

    resampled_x = np.linspace(np.min(x), np.max(x), n, endpoint=True)
    resampled_y = interpolator(resampled_x)

    return resampled_x, resampled_y


class ElevationProfileParamsProtocol(Protocol):
    """Protocol for Elevation Profile Parameters."""
    @property
    def profile_scatter_params(self) -> dict[ScatterPointCategory, ScatterParams]: ...  # noqa: D102
    profile_fill_color: str
    profile_font_color: str
    profile_font_size: A4Float
    profile_fontproperties: FontProperties

    user_uphill_m: int | None
    user_dist_km: float | None


@dataclass
class ElevationProfile:
    """Draw the elevation profile, the scatter points and the statistics.

    N.B. The elevation profile is stored in relative coordinates in [0, 1] for both latitude and longitude.
    Which allows to draw it for any GPX bounds.

      Lat
      ▲
    1 | ┌─────┐
      │ │     │
      │ │     │
      │ └─────┘
    0 └─────────► Lon
      0       1
    """
    bounds: GpxBounds
    scatter_indices: dict[ScatterPointCategory, list[int]]
    rel_poly_lat: np.ndarray  # in [0, 1]
    rel_poly_lon: np.ndarray  # in [0, 1]
    rel_text_lat: float  # in [0, 1]

    true_dist_km: float
    true_uphill_m: int

    @staticmethod
    def from_track(bounds: GpxBounds,
                   track: GpxTrack,
                   points: list[ScatterPoint],
                   ele_ratio: float,
                   n_points: int = 1000) -> 'ElevationProfile':
        """Initialize the Elevation Profile from a GPX Track and a list of Scatter Points."""
        # Draw Elevation Over Distance
        normalized_poly_lon = np.array(track.list_cumul_dist_km)/track.list_cumul_dist_km[-1]  # in [0, 1]
        min_ele, max_ele = min(track.list_ele_m), max(track.list_ele_m)
        normalized_poly_lat = (np.array(track.list_ele_m) - min_ele) / (max_ele - min_ele)  # in [0, 1]

        rel_poly_lat = (1.0-ele_ratio) + ele_ratio * normalized_poly_lat
        rel_poly_lon = normalized_poly_lon

        rel_poly_lon, rel_poly_lat = downsample(x=rel_poly_lon, y=rel_poly_lat, n=n_points)
        n_points = min(n_points, len(rel_poly_lon))

        # Find the indices of the scatter points
        scatter_indices: dict[ScatterPointCategory, list[int]] = defaultdict(list)
        distances = get_pairwise_distance_m(lonlat_1=np.array([[sp.lon, sp.lat] for sp in points]),
                                            lonlat_2=np.stack([track.list_lon, track.list_lat], axis=-1))
        float_argmin_indices = np.argmin(distances, axis=-1) * float(n_points)/len(track)

        for scatter, i in zip(points, float_argmin_indices):
            i_int = math.floor(i)
            if scatter.category is ScatterPointCategory.START:
                i_int = 0
            elif scatter.category is ScatterPointCategory.END:
                i_int = n_points - 1
            scatter_indices[scatter.category].append(i_int)

        # Build the full polygon (Append the points to keep valid the scatter indices)
        rel_poly_lat = np.concatenate((rel_poly_lat, np.array([1-ele_ratio, 0., 0., 1-ele_ratio])))
        rel_poly_lon = np.concatenate((rel_poly_lon, np.array([1., 1., 0., 0.])))

        # Text
        rel_text_lat = 0.5 * (1.0 - ele_ratio)
        return ElevationProfile(bounds=bounds, scatter_indices=dict(scatter_indices),
                                rel_poly_lat=rel_poly_lat, rel_poly_lon=rel_poly_lon, rel_text_lat=rel_text_lat,
                                true_uphill_m=int(track.uphill_m), true_dist_km=track.dist_km)

    def change_papersize(self, paper: PaperSize, bounds: GpxBounds) -> None:
        """Change Paper Size and GPX Bounds."""
        self.bounds = bounds

    def draw(self, fig: DrawingFigure, params: ElevationProfileParamsProtocol) -> None:
        """Draw the elevation profile, the scatter points and the statistics."""
        # Polygon
        list_lon = self.bounds.lon_min + self.rel_poly_lon*self.bounds.dlon
        list_lat = self.bounds.lat_min + self.rel_poly_lat*self.bounds.dlat
        fig.fill(list_lon=list_lon, list_lat=list_lat, color=params.profile_fill_color, alpha=1.0)

        # Scatter
        for category, indices in self.scatter_indices.items():
            assert_in(category, params.profile_scatter_params)
            scatter_params = params.profile_scatter_params[category]
            fig.scatter(list_lat=list_lat[indices], list_lon=list_lon[indices], color=scatter_params.color,
                        marker=scatter_params.marker, markersize=scatter_params.markersize)

        # Text
        text_lat = self.bounds.lat_min + self.rel_text_lat*self.bounds.dlat
        dist_km = get(params.user_dist_km, self.true_dist_km)
        uphill_m = get(params.user_uphill_m, self.true_uphill_m)
        fig.text(lon=self.bounds.lon_center, lat=text_lat,
                 s=f"{dist_km:.2f} km - {uphill_m:d} m D+",
                 color=params.profile_font_color,
                 fontsize=params.profile_font_size,
                 font=params.profile_fontproperties, ha="center", va="center")
