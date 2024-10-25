#!/usr/bin/python3
"""Work in progress. Generate a poster from a urban marathon GPX track."""
import os

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.drawing.drawing_data import BaseDrawingData
from pretty_gpx.common.drawing.drawing_data import LineCollectionData
from pretty_gpx.common.drawing.drawing_data import PlotData
from pretty_gpx.common.drawing.drawing_data import PolygonCollectionData
from pretty_gpx.common.drawing.drawing_data import ScatterData
from pretty_gpx.common.drawing.drawing_data import TextData
from pretty_gpx.common.drawing.elevation_stats_section import ElevationStatsSection
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.paths import FONTS_DIR
from pretty_gpx.common.utils.paths import RUNNING_DIR
from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.common.utils.utils import format_timedelta
from pretty_gpx.common.utils.utils import mm_to_point
from pretty_gpx.rendering_modes.city.city_drawing_figure import CityDrawingFigure
from pretty_gpx.rendering_modes.city.city_vertical_layout import CityVerticalLayout
from pretty_gpx.rendering_modes.city.data.forests import prepare_download_city_forests
from pretty_gpx.rendering_modes.city.data.forests import process_city_forests
from pretty_gpx.rendering_modes.city.data.rivers import prepare_download_city_rivers
from pretty_gpx.rendering_modes.city.data.rivers import process_city_rivers
from pretty_gpx.rendering_modes.city.data.roads import prepare_download_city_roads
from pretty_gpx.rendering_modes.city.data.roads import process_city_roads
from pretty_gpx.rendering_modes.city.drawing.city_drawing_params import CityLinewidthParams
from pretty_gpx.rendering_modes.city.drawing.theme_colors import DARK_COLOR_THEMES
from pretty_gpx.rendering_modes.city.drawing.theme_colors import LIGHT_COLOR_THEMES
from pretty_gpx.rendering_modes.city.drawing.theme_colors import ThemeColors


def plot(gpx_track: GpxTrack, theme_colors: ThemeColors) -> None:
    """Plot a GPX track on a city map."""
    paper = PAPER_SIZES['A4']
    if gpx_track.duration_s is not None:
        layout = CityVerticalLayout.two_lines_stats()
    else:
        layout = CityVerticalLayout.default()
    roads_bounds, base_plotter = layout.get_download_bounds_and_paper_figure(gpx_track, paper)

    caracteristic_distance_m = roads_bounds.diagonal_m
    logger.info(f"Domain diagonal is {caracteristic_distance_m/1000.:.1f}km")
    city_linewidth = CityLinewidthParams.default(paper_size=paper,
                                                 diagonal_distance_m=caracteristic_distance_m)

    total_query = OverpassQuery()

    # Add the queries to the overpass_query class to run all queries at once

    for prepare_func in [prepare_download_city_roads,
                         prepare_download_city_rivers,
                         prepare_download_city_forests]:

        prepare_func(query=total_query, bounds=roads_bounds)

    # Merge and run all queries
    total_query.launch_queries()

    # Retrieve the data
    roads = process_city_roads(query=total_query,
                               bounds=roads_bounds)

    rivers = process_city_rivers(query=total_query,
                                 bounds=roads_bounds)

    forests, farmland = process_city_forests(query=total_query,
                                             bounds=roads_bounds)
    forests.interior_polygons = []

    track_data: list[BaseDrawingData] = [PlotData(x=gpx_track.list_lon, y=gpx_track.list_lat, linewidth=2.0)]
    road_data: list[BaseDrawingData] = []
    point_data: list[BaseDrawingData] = []
    rivers_data: list[PolygonCollectionData] = [PolygonCollectionData(polygons=rivers)]
    forests_data: list[PolygonCollectionData] = [PolygonCollectionData(polygons=forests)]
    farmland_data: list[PolygonCollectionData] = [PolygonCollectionData(polygons=farmland)]

    for priority, way in roads.items():
        road_data.append(LineCollectionData(way, linewidth=city_linewidth.linewidth_priority[priority], zorder=1))

    title_txt = "Route des 4 chateaux"
    b = base_plotter.gpx_bounds
    title = TextData(x=b.lon_center, y=b.lat_max - 0.8 * b.dlat * layout.title_relative_h,
                     s=title_txt, fontsize=mm_to_point(20.0),
                     fontproperties=FontProperties(fname=os.path.join(FONTS_DIR, "Lobster 1.4.otf")),
                     ha="center",
                     va="center")

    stats_text = f"{gpx_track.list_cumul_dist_km[-1]:.2f} km - {int(gpx_track.uphill_m)} m D+"

    if gpx_track.duration_s is not None:
        stats_text += f"\n{format_timedelta(gpx_track.duration_s)}"

    point_data.append(ScatterData(x=[gpx_track.list_lon[0]], y=[gpx_track.list_lat[0]],
                                  marker="o", markersize=mm_to_point(3.5)))
    point_data.append(ScatterData(x=[gpx_track.list_lon[-1]], y=[gpx_track.list_lat[-1]],
                                  marker="s", markersize=mm_to_point(3.5)))

    ele = ElevationStatsSection(layout, base_plotter, gpx_track)
    track_data.append(ele.fill_poly)
    stats = TextData(x=ele.section_center_lon_x, y=ele.section_center_lat_y,
                     s=stats_text, fontsize=mm_to_point(18.5),
                     fontproperties=FontProperties(fname=os.path.join(FONTS_DIR, "Lobster 1.4.otf")),
                     ha="center",
                     va="center")

    plotter = CityDrawingFigure(paper_size=base_plotter.paper_size,
                                latlon_aspect_ratio=base_plotter.latlon_aspect_ratio,
                                gpx_bounds=base_plotter.gpx_bounds,
                                w_display_pix=800,
                                track_data=track_data,
                                road_data=road_data,
                                point_data=point_data,
                                rivers_data=rivers_data,
                                forests_data=forests_data,
                                farmland_data=farmland_data,
                                title=title,
                                stats=stats)

    fig, ax = plt.subplots(figsize=(10, 10))

    plotter.draw(fig=fig,
                 ax=ax,
                 theme_colors=theme_colors,
                 stats_txt=stats_text,
                 title_txt=title_txt)

    plt.show()


if __name__ == "__main__":
    gpx_track = GpxTrack.load(os.path.join(RUNNING_DIR, "route_4_chateaux.gpx"))
    for theme in list(DARK_COLOR_THEMES.values())+list(LIGHT_COLOR_THEMES.values()):
        plot(gpx_track, theme)
    Profiling.export_events()
