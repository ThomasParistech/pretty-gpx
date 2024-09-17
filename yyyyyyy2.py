import os

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.font_manager import FontProperties

from pretty_gpx.city.city_roads import CityRoadType
from pretty_gpx.city.city_roads import download_city_roads
from pretty_gpx.city.city_vertical_layout import CityVerticalLayout
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.utils.paths import FONTS_DIR
from pretty_gpx.mountain.drawing.theme_colors import DARK_COLOR_THEMES
from pretty_gpx.mountain.drawing.theme_colors import LIGHT_COLOR_THEMES
from pretty_gpx.mountain.drawing.theme_colors import ThemeColors


def plot(gpx_track: GpxTrack, theme_colors: ThemeColors):
    if theme_colors.dark_mode:
        background_color = "black"
        road_color = theme_colors.background_color
    else:
        background_color = theme_colors.background_color
        road_color = "white"

    background_color, road_color = road_color, background_color  # FIXME

    roads_bounds, plotter = CityVerticalLayout().get_download_bounds_and_paper_figure(gpx_track, PAPER_SIZES['A4'])

    roads = download_city_roads(roads_bounds)
    linewidth_priority = {
        CityRoadType.HIGHWAY: 1.0,
        CityRoadType.SECONDARY_ROAD: 0.5,
        CityRoadType.STREET: 0.25,
        CityRoadType.ACCESS_ROAD: 0.1
    }
    fig, ax = plt.subplots(figsize=(10, 10))

    plotter.setup(fig, ax)
    plotter.adjust_display_width(fig, 800)

    ax.set_facecolor(background_color)
    for priority, way in roads.items():
        lines_collection = LineCollection(way, lw=linewidth_priority[priority], colors=road_color)
        ax.add_collection(lines_collection)

    plt.plot(gpx_track.list_lon, gpx_track.list_lat, color=theme_colors.track_color)

    plt.text(gpx_track.list_lon[0], gpx_track.list_lat[0], "Start", color=theme_colors.peak_color)
    plt.text(gpx_track.list_lon[-1], gpx_track.list_lat[-1], "End", color=theme_colors.peak_color)

    plt.text(roads_bounds.lon_center,
             roads_bounds.lat_min + 0.8*roads_bounds.dlat,
             "Marathon de Paris", color=theme_colors.peak_color, ha="center", va="center",
             fontsize=40,
             fontproperties=FontProperties(fname=os.path.join(FONTS_DIR, "Lobster 1.4.otf")))

    plt.show()


if __name__ == "__main__":
    gpx_track = GpxTrack.load("data/marathon.gpx")
    for theme in list(DARK_COLOR_THEMES.values())+list(LIGHT_COLOR_THEMES.values()):
        plot(gpx_track, theme)
