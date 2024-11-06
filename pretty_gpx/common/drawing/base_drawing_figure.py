#!/usr/bin/python3
"""Base Drawing Figure."""
from dataclasses import dataclass

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.asserts import assert_ge
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.utils import mm_to_inch


@dataclass
class BaseDrawingFigure:
    """Base Drawing Figure."""
    paper_size: PaperSize
    latlon_aspect_ratio: float
    gpx_bounds: GpxBounds

    def get_scale(self) -> float:
        """Get the scale of the drawing, i.e. ratio between real meters and drawing millimeters."""
        dx_m, dy_m = self.gpx_bounds.dx_dy_m
        w_mm = self.paper_size.w_mm - 2*self.paper_size.margin_mm
        h_mm = self.paper_size.h_mm - 2*self.paper_size.margin_mm
        return 0.5 * (dx_m/w_mm + dy_m/h_mm)

    @profile
    def setup(self, fig: Figure, ax: Axes) -> None:
        """Setup the figure with the appropriate aspect-ratio, xlim/ylim, size in inches and dpi."""
        ax.cla()
        ax.axis('off')

        ax.add_artist(ax.patch)  # Keep the background color if set with ax.set_facecolor
        ax.patch.set_zorder(-1)

        fig.tight_layout(pad=0)

        ax.set_xlim((self.gpx_bounds.lon_min, self.gpx_bounds.lon_max))
        ax.set_ylim((self.gpx_bounds.lat_min, self.gpx_bounds.lat_max))

        ax.set_aspect(self.latlon_aspect_ratio)

        w_inches = mm_to_inch(self.paper_size.w_mm)
        h_inches = mm_to_inch(self.paper_size.h_mm)

        margin_inches = mm_to_inch(self.paper_size.margin_mm)

        fig.set_size_inches(w_inches, h_inches)

        fig.subplots_adjust(left=margin_inches/w_inches, right=1-margin_inches/w_inches,
                            bottom=margin_inches/h_inches, top=1-margin_inches/h_inches)

        ax.autoscale(False)

    def imshow(self, ax: Axes, img: np.ndarray, img_gpx_bounds: GpxBounds) -> None:
        """Plot the background image."""
        h, w = img.shape[:2]

        ratio_img = w/h
        ratio_bounds = img_gpx_bounds.dlon/img_gpx_bounds.dlat

        assert_ge(min(ratio_img/ratio_bounds, ratio_bounds/ratio_img), 0.9,
                  msg=f"Image and GpxBounds have different aspect-ratios: {ratio_img: .2f} and {ratio_bounds: .2f}")

        ax.imshow(img,
                  extent=(img_gpx_bounds.lon_min, img_gpx_bounds.lon_max,
                          img_gpx_bounds.lat_min, img_gpx_bounds.lat_max),
                  aspect=self.latlon_aspect_ratio)
