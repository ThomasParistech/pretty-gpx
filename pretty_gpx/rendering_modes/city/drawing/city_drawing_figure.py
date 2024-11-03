#!/usr/bin/python3
"""City Drawing Figure."""
from dataclasses import dataclass

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pretty_gpx.common.drawing.drawing_data import BaseDrawingData
from pretty_gpx.common.drawing.drawing_data import PolygonCollectionData
from pretty_gpx.common.drawing.drawing_data import TextData
from pretty_gpx.common.drawing.elevation_stats_section import ElevationStatsSection
from pretty_gpx.common.structure import DrawingFigure
from pretty_gpx.common.structure import DrawingParams
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.rendering_modes.city.city_vertical_layout import CityVerticalLayout
from pretty_gpx.rendering_modes.city.drawing.city_colors import CityColors


@dataclass(frozen=True)
class CityDrawingParams(DrawingParams):
    """Drawing data for the poster."""
    theme_colors: CityColors
    title_txt: str
    stats_txt: str
    layout: CityVerticalLayout


@dataclass
class CityDrawingFigure(DrawingFigure[CityDrawingParams]):
    """Drawing Figure displaying annotations on top of an image plotted with plt.imshow.

    track_data: Drawing Data to plot with the Track Color
    peak_data: Drawing Data to plot with the Peak Color

    title: Text Drawing Data for the title at the top of the image (Text String can be updated)
    stats: Text Drawing Data for the statistics at the bottom of the image (Text String can be updated)
    """
    track_data: list[BaseDrawingData]
    road_data: list[BaseDrawingData]
    point_data: list[BaseDrawingData]
    rivers_data: list[PolygonCollectionData]
    forests_data: list[PolygonCollectionData]
    farmland_data: list[PolygonCollectionData]
    elevation_profile: ElevationStatsSection

    title: TextData
    stats: TextData

    @profile
    def draw(self, fig: Figure, ax: Axes, params: CityDrawingParams) -> None:
        """Plot the annotations."""
        road_color = "black" if params.theme_colors.dark_mode else "white"

        old_layout = self.elevation_profile.layout
        new_layout = params.layout

        if old_layout != new_layout:
            self.elevation_profile.update_section_with_new_layout(self,
                                                                  new_layout=new_layout)
            self.stats.y = self.gpx_bounds.lat_min + 0.5 * self.gpx_bounds.dlat * new_layout.stats_relative_h

        self.setup(fig, ax)

        self.title.s = params.title_txt
        self.stats.s = params.stats_txt

        for surface_data1 in self.farmland_data:
            surface_data1.plot(ax, params.theme_colors.farmland_color, params.theme_colors.background_color)

        for surface_data2 in self.forests_data:
            surface_data2.plot(ax, params.theme_colors.forests_color, params.theme_colors.farmland_color)

        for surface_data3 in self.rivers_data:
            surface_data3.plot(ax, params.theme_colors.rivers_color, params.theme_colors.background_color)

        for data4 in self.road_data:
            data4.plot(ax, road_color)

        for data5 in self.track_data:
            data5.plot(ax, params.theme_colors.track_color)

        for data6 in self.point_data:
            data6.plot(ax, params.theme_colors.point_color)

        self.elevation_profile.fill_poly.plot(ax, params.theme_colors.track_color)

        ax.set_facecolor(params.theme_colors.background_color)

        self.title.plot(ax, params.theme_colors.point_color)
        self.stats.plot(ax, params.theme_colors.background_color)
