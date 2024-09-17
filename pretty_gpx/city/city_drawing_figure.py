#!/usr/bin/python3
"""City Drawing Figure."""
from dataclasses import dataclass

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pretty_gpx.common.drawing.base_drawing_figure import BaseDrawingFigure
from pretty_gpx.common.drawing.drawing_data import BaseDrawingData
from pretty_gpx.common.drawing.drawing_data import TextData
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.mountain.drawing.theme_colors import ThemeColors


@dataclass
class CityDrawingFigure(BaseDrawingFigure):
    """Drawing Figure displaying annotations on top of an image plotted with plt.imshow.

    w_display_pix: Expected screen Figure width in pixels (when displayed on screen)

    track_data: Drawing Data to plot with the Track Color
    peak_data: Drawing Data to plot with the Peak Color

    title: Text Drawing Data for the title at the top of the image (Text String can be updated)
    stats: Text Drawing Data for the statistics at the bottom of the image (Text String can be updated)

    img_gpx_bounds: Extent of the image to plot inside the figure
    """
    w_display_pix: int

    track_data: list[BaseDrawingData]
    road_data: list[BaseDrawingData]

    # title: TextData
    # stats: TextData

    def draw(self,
             fig: Figure,
             ax: Axes,
             background_color: str,
             road_color: str,
             track_color: str,
             #  title_txt: str,
             #  stats_txt: str
             ) -> None:
        """Plot the background image and the annotations on top of it."""
        self.setup(fig, ax)
        self.adjust_display_width(fig, self.w_display_pix)

        # self.title.s = title_txt
        # self.stats.s = stats_txt

        for data in self.road_data:
            data.plot(ax, road_color)

        for data in self.track_data:
            data.plot(ax, track_color)

        ax.set_facecolor(background_color)

        # self.title.plot(ax, theme_colors.peak_color)
        # self.stats.plot(ax, theme_colors.background_color)
