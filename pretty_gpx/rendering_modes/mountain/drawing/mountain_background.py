#!/usr/bin/python3
"""Drawing Component for a Mountain Background."""
from dataclasses import dataclass
from typing import Final
from typing import Protocol

import numpy as np

from pretty_gpx.common.drawing.utils.color_theme import hex_to_rgb
from pretty_gpx.common.drawing.utils.drawing_figure import DrawingFigure
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.asserts import assert_in_range
from pretty_gpx.common.utils.asserts import assert_lt
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.utils import mm_to_inch
from pretty_gpx.common.utils.utils import safe
from pretty_gpx.rendering_modes.mountain.data.elevation_map import download_elevation_map
from pretty_gpx.rendering_modes.mountain.data.elevation_map import rescale_elevation
from pretty_gpx.rendering_modes.mountain.drawing.hillshading import CachedHillShading

MOUNTAIN_LOW_RES_DPI: Final[int] = 50
HIGH_RES_DPI = 400


class MountainBackgroundParamsProtocol(Protocol):
    """Protocol for Mountain Background Parameters."""
    mountain_background_color: str
    mountain_dark_mode: bool
    mountain_azimuth: int


@dataclass(kw_only=True)
class MountainBackground:
    """Drawing Component for a Mountain Background."""
    union_bounds: GpxBounds
    full_elevation_map: np.ndarray
    low_res_elevation: CachedHillShading | None
    high_res_elevation: CachedHillShading | None

    @staticmethod
    @profile
    def from_union_bounds(union_bounds: GpxBounds) -> 'MountainBackground':
        """Initialize the Mountain Background from the Union Bounds."""
        full_elevation_map = download_elevation_map(union_bounds)
        return MountainBackground(union_bounds=union_bounds, full_elevation_map=full_elevation_map,
                                  low_res_elevation=None, high_res_elevation=None)

    @profile
    def change_papersize(self, paper: PaperSize, bounds: GpxBounds) -> None:
        """Change Paper Size and GPX Bounds."""
        rel_lat_min = (bounds.lat_min - self.union_bounds.lat_min) / self.union_bounds.dlat
        rel_lat_max = (bounds.lat_max - self.union_bounds.lat_min) / self.union_bounds.dlat

        rel_lon_min = (bounds.lon_min - self.union_bounds.lon_min) / self.union_bounds.dlon
        rel_lon_max = (bounds.lon_max - self.union_bounds.lon_min) / self.union_bounds.dlon

        assert_in_range(rel_lat_min, 0, 1)
        assert_in_range(rel_lat_max, 0, 1)
        assert_in_range(rel_lon_min, 0, 1)
        assert_in_range(rel_lon_max, 0, 1)

        h, w = self.full_elevation_map.shape[:2]
        elevation_map = self.full_elevation_map[int(rel_lat_min*h):int(rel_lat_max*h),
                                                int(rel_lon_min*w):int(rel_lon_max*w)]

        assert_lt(MOUNTAIN_LOW_RES_DPI, HIGH_RES_DPI)
        current_dpi = elevation_map.shape[0] / mm_to_inch(paper.h_mm-2*paper.margin_mm)
        self.low_res_elevation = CachedHillShading(rescale_elevation(elevation_map, MOUNTAIN_LOW_RES_DPI/current_dpi))
        self.high_res_elevation = CachedHillShading(rescale_elevation(elevation_map, HIGH_RES_DPI/current_dpi))

    @profile
    def draw(self, fig: DrawingFigure, params: MountainBackgroundParamsProtocol, high_resolution: bool) -> None:
        """Draw the shaded elevation map."""
        if high_resolution:
            elevation_shading = self.high_res_elevation
        else:
            elevation_shading = self.low_res_elevation
        grey_hillshade = safe(elevation_shading).render_grey(params.mountain_azimuth)[..., None]
        background_color_rgb = hex_to_rgb(params.mountain_background_color)
        color_0 = (0, 0, 0) if params.mountain_dark_mode else background_color_rgb
        color_1 = background_color_rgb if params.mountain_dark_mode else (255, 255, 255)
        colored_hillshade = grey_hillshade * (np.array(color_1) - np.array(color_0)) + np.array(color_0)

        fig.imshow(img=colored_hillshade.astype(np.uint8))
