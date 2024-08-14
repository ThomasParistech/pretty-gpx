#!/usr/bin/python3
"""Drawing Figure."""
from dataclasses import dataclass

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pretty_gpx.drawing.drawing_data import BaseDrawingData
from pretty_gpx.drawing.drawing_data import TextData
from pretty_gpx.drawing.theme_colors import ThemeColors
from pretty_gpx.utils import mm_to_inch


@dataclass
class BaseDrawingFigure:
    """Base Drawing Figure displaying an image with plt.imshow.

    w_mm: Expected intrinsic Figure width in mm (when saved as a vectorized image)
    """
    w_mm: float
    latlon_aspect_ratio: float

    def imshow(self,
               fig: Figure,
               ax: Axes,
               img: np.ndarray) -> None:
        """Display the image, with the appropriate size in inches and dpi."""
        h, w = img.shape[:2]
        ax.cla()
        ax.axis('off')
        fig.tight_layout(pad=0)
        ax.imshow(img)
        ax.set_aspect(self.latlon_aspect_ratio)

        w_inches = mm_to_inch(self.w_mm)
        fig.set_size_inches(w_inches, self.latlon_aspect_ratio*h * w_inches/w)

        ax.autoscale(False)

    def adjust_display_width(self, fig: Figure, w_display_pix: int) -> None:
        """Adjust width in pixels on the screen of the displayed figure."""
        fig.set_dpi(w_display_pix / mm_to_inch(self.w_mm))


@dataclass
class DrawingFigure(BaseDrawingFigure):
    """Drawing Figure displaying annotations on top of an image plotted with plt.imshow.

    w_display_pix: Expected screen Figure width in pixels (when displayed on screen)
    ref_img_shape: Shape of the reference background image. It defines the scale at which the X-Y coordinates of the
        annotations have been saved.

    track_data: Drawing Data to plot with the Track Color
    peak_data: Drawing Data to plot with the Peak Color

    title: Text Drawing Data for the title at the top of the image (Text String can be updated)
    stats: Text Drawing Data for the statistics at the bottom of the image (Text String can be updated)
    """
    w_display_pix: int
    ref_img_shape: tuple[int, ...]

    track_data: list[BaseDrawingData]
    peak_data: list[BaseDrawingData]

    title: TextData
    stats: TextData

    def draw(self,
             fig: Figure,
             ax: Axes,
             img: np.ndarray,
             theme_colors: ThemeColors,
             title_txt: str,
             stats_txt: str) -> None:
        """Plot the background image and the annotations on top of it."""
        self.imshow(fig, ax, img)
        self.adjust_display_width(fig, self.w_display_pix)

        self.title.s = title_txt
        self.stats.s = stats_txt

        for data in self.track_data:
            data.plot(ax, theme_colors.track_color, self.ref_img_shape, img.shape)

        for data in self.peak_data:
            data.plot(ax, theme_colors.peak_color, self.ref_img_shape, img.shape)

        self.title.plot(ax, theme_colors.peak_color, self.ref_img_shape, img.shape)
        self.stats.plot(ax, theme_colors.background_color, self.ref_img_shape, img.shape)
