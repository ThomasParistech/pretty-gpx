#!/usr/bin/python3
"""Work in progress. Generate a poster from a urban marathon GPX track."""
import os

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from pretty_gpx.city.city_drawing_figure import CityDrawingFigure
from pretty_gpx.city.city_vertical_layout import CityVerticalLayout
from pretty_gpx.city.data.roads import CityRoadType
from pretty_gpx.city.data.roads import download_city_roads
from pretty_gpx.common.drawing.drawing_data import BaseDrawingData
from pretty_gpx.common.drawing.drawing_data import LineCollectionData
from pretty_gpx.common.drawing.drawing_data import PlotData
from pretty_gpx.common.drawing.drawing_data import PolyFillData
from pretty_gpx.common.drawing.drawing_data import ScatterData
from pretty_gpx.common.drawing.drawing_data import TextData
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.utils.paths import FONTS_DIR
from pretty_gpx.common.utils.utils import mm_to_point
from pretty_gpx.mountain.drawing.theme_colors import DARK_COLOR_THEMES
from pretty_gpx.mountain.drawing.theme_colors import LIGHT_COLOR_THEMES
from pretty_gpx.mountain.drawing.theme_colors import ThemeColors


def plot(gpx_track: GpxTrack, theme_colors: ThemeColors):
    """Plot a GPX track on a city map."""
    if theme_colors.dark_mode:
        background_color = theme_colors.background_color
        road_color = "black"
    else:
        background_color = theme_colors.background_color
        road_color = "white"

    track_color = theme_colors.track_color

    paper = PAPER_SIZES['A4']
    layout = CityVerticalLayout()
    roads_bounds, base_plotter = layout.get_download_bounds_and_paper_figure(gpx_track, paper)

    roads = download_city_roads(roads_bounds)
    linewidth_priority = {
        CityRoadType.HIGHWAY: 1.0,
        CityRoadType.SECONDARY_ROAD: 0.5,
        CityRoadType.STREET: 0.25,
        CityRoadType.ACCESS_ROAD: 0.1
    }

    track_data: list[BaseDrawingData] = []
    road_data: list[BaseDrawingData] = []
    peak_data: list[BaseDrawingData] = []

    track_data.append(PlotData(x=gpx_track.list_lon, y=gpx_track.list_lat, linewidth=2.0))

    for priority, way in roads.items():
        road_data.append(LineCollectionData(way, linewidth=linewidth_priority[priority], zorder=1))

    b = base_plotter.gpx_bounds
    title = TextData(x=b.lon_center, y=b.lat_max - 0.8 * b.dlat * layout.title_relative_h,
                     s="Marathon de Paris", fontsize=mm_to_point(20.0),
                     fontproperties=FontProperties(fname=os.path.join(FONTS_DIR, "Lobster 1.4.otf")),
                     ha="center")
    stats_text = f"{gpx_track.list_cumul_dist_km[-1]:.2f} km - {int(gpx_track.uphill_m)} m D+"
    stats = TextData(x=b.lon_center, y=b.lat_min + 0.5 * b.dlat * layout.stats_relative_h,
                     s=stats_text, fontsize=mm_to_point(18.5),
                     fontproperties=FontProperties(fname=os.path.join(FONTS_DIR, "Lobster 1.4.otf")),
                     ha="center")
    peak_data.append(ScatterData(x=[gpx_track.list_lon[0]], y=[gpx_track.list_lat[0]],
                                 marker="o", markersize=mm_to_point(3.5)))
    peak_data.append(ScatterData(x=[gpx_track.list_lon[-1]], y=[gpx_track.list_lat[-1]],
                                 marker="s", markersize=mm_to_point(3.5)))

    h_top_stats = b.lat_min + b.dlat * layout.stats_relative_h
    track_data.append(PolyFillData(x=[b.lon_min, b.lon_max, b.lon_max, b.lon_min],
                                   y=[h_top_stats, h_top_stats, b.lat_min, b.lat_min]))

    plotter = CityDrawingFigure(paper_size=base_plotter.paper_size,
                                latlon_aspect_ratio=base_plotter.latlon_aspect_ratio,
                                gpx_bounds=base_plotter.gpx_bounds,
                                w_display_pix=800,
                                track_data=track_data,
                                road_data=road_data,
                                peak_data=peak_data,
                                title=title,
                                stats=stats)

    fig, ax = plt.subplots(figsize=(10, 10))

    plotter.draw(fig, ax, background_color, road_color, track_color, theme_colors.peak_color)

    plt.show()


if __name__ == "__main__":
    gpx_track = GpxTrack.load("data/marathon.gpx")
    for theme in list(DARK_COLOR_THEMES.values())+list(LIGHT_COLOR_THEMES.values()):
        plot(gpx_track, theme)
