#!/usr/bin/python3
"""Mountain Drawing Figure."""
from dataclasses import dataclass

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pretty_gpx.common.drawing.drawing_data import BaseDrawingData
from pretty_gpx.common.drawing.drawing_data import TextData
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.structure import DrawingFigure
from pretty_gpx.common.structure import DrawingParams
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.rendering_modes.mountain.drawing.mountain_colors import MountainColors


@dataclass(frozen=True)
class MountainDrawingParams(DrawingParams):
    """Drawing data for the poster."""
    img: np.ndarray
    theme_colors: MountainColors
    title_txt: str
    stats_txt: str


@dataclass
class MountainDrawingFigure(DrawingFigure[MountainDrawingParams]):
    """Drawing Figure displaying annotations on top of an image plotted with plt.imshow.

    track_data: Drawing Data to plot with the Track Color
    peak_data: Drawing Data to plot with the Peak Color

    title: Text Drawing Data for the title at the top of the image (Text String can be updated)
    stats: Text Drawing Data for the statistics at the bottom of the image (Text String can be updated)

    img_gpx_bounds: Extent of the image to plot inside the figure
    """
    track_data: list[BaseDrawingData]
    peak_data: list[BaseDrawingData]

    title: TextData
    stats: TextData

    img_gpx_bounds: GpxBounds

    @profile
    def draw(self, fig: Figure, ax: Axes, params: MountainDrawingParams) -> None:
        """Plot the background image and the annotations on top of it."""
        self.setup(fig, ax)

        self.imshow(ax, params.img, self.img_gpx_bounds)

        self.title.s = params.title_txt
        self.stats.s = params.stats_txt

        for data in self.track_data:
            data.plot(ax, params.theme_colors.track_color)

        for data in self.peak_data:
            data.plot(ax, params.theme_colors.peak_color)

        self.title.plot(ax, params.theme_colors.peak_color)
        self.stats.plot(ax, params.theme_colors.background_color)
