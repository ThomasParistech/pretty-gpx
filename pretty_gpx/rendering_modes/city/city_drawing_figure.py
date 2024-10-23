#!/usr/bin/python3
"""City Drawing Figure."""
from dataclasses import dataclass

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pretty_gpx.common.drawing.base_drawing_figure import BaseDrawingFigure
from pretty_gpx.common.drawing.drawing_data import BaseDrawingData
from pretty_gpx.common.drawing.drawing_data import PolygonCollectionData
from pretty_gpx.common.drawing.drawing_data import TextData
from pretty_gpx.rendering_modes.city.drawing.theme_colors import ThemeColors


@dataclass
class CityDrawingFigure(BaseDrawingFigure):
    """Drawing Figure displaying annotations on top of an image plotted with plt.imshow.

    w_display_pix: Expected screen Figure width in pixels (when displayed on screen)

    track_data: Drawing Data to plot with the Track Color
    peak_data: Drawing Data to plot with the Peak Color

    title: Text Drawing Data for the title at the top of the image (Text String can be updated)
    stats: Text Drawing Data for the statistics at the bottom of the image (Text String can be updated)
    """
    w_display_pix: int

    track_data: list[BaseDrawingData]
    road_data: list[BaseDrawingData]
    point_data: list[BaseDrawingData]
    rivers_data: list[PolygonCollectionData]
    forests_data: list[PolygonCollectionData]
    farmland_data: list[PolygonCollectionData]

    title: TextData
    stats: TextData

    def draw(self,
             fig: Figure,
             ax: Axes,
             theme_colors: ThemeColors
             ) -> None:
        """Plot the background image and the annotations on top of it."""
        road_color = "black" if theme_colors.dark_mode else "white"


        self.setup(fig, ax)
        self.adjust_display_width(fig, self.w_display_pix)

        for surface_data in self.rivers_data:
            surface_data.plot(ax, theme_colors.rivers_color, theme_colors.background_color)

        for surface_data in self.farmland_data:
            surface_data.plot(ax, theme_colors.farmland_color, theme_colors.background_color)

        for surface_data in self.forests_data:
            surface_data.plot(ax, theme_colors.forests_color, theme_colors.farmland_color)

        for data in self.road_data:
            data.plot(ax, road_color)

        for data in self.track_data:
            data.plot(ax, theme_colors.track_color)

        for data in self.point_data:
            data.plot(ax, theme_colors.point_color)

        ax.set_facecolor(theme_colors.background_color)

        self.title.plot(ax, theme_colors.point_color)
        self.stats.plot(ax, theme_colors.background_color)
