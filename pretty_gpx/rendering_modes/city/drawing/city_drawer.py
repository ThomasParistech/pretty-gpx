#!/usr/bin/python3
"""City Drawer."""
from dataclasses import dataclass

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.drawing.base_drawing_figure import BaseDrawingFigure
from pretty_gpx.common.drawing.drawing_data import BaseDrawingData
from pretty_gpx.common.drawing.drawing_data import LineCollectionData
from pretty_gpx.common.drawing.drawing_data import PlotData
from pretty_gpx.common.drawing.drawing_data import PolyFillData
from pretty_gpx.common.drawing.drawing_data import PolygonCollectionData
from pretty_gpx.common.drawing.drawing_data import ScatterData
from pretty_gpx.common.drawing.drawing_data import TextData
from pretty_gpx.common.drawing.elevation_stats_section import ElevationStatsSection
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.utils import format_timedelta
from pretty_gpx.common.utils.utils import mm_to_point
from pretty_gpx.rendering_modes.city.city_vertical_layout import CityVerticalLayout
from pretty_gpx.rendering_modes.city.data.city_augmented_gpx_data import CityAugmentedGpxData
from pretty_gpx.rendering_modes.city.data.forests import prepare_download_city_forests
from pretty_gpx.rendering_modes.city.data.forests import process_city_forests
from pretty_gpx.rendering_modes.city.data.rivers import prepare_download_city_rivers
from pretty_gpx.rendering_modes.city.data.rivers import process_city_rivers
from pretty_gpx.rendering_modes.city.data.roads import prepare_download_city_roads
from pretty_gpx.rendering_modes.city.data.roads import process_city_roads
from pretty_gpx.rendering_modes.city.drawing.city_colors import CityColors
from pretty_gpx.rendering_modes.city.drawing.city_drawing_figure import CityDrawingFigure
from pretty_gpx.rendering_modes.city.drawing.city_drawing_params import CityDrawingStyleParams
from pretty_gpx.rendering_modes.city.drawing.city_drawing_params import CityLinewidthParams
from pretty_gpx.ui.pages.template.ui_plot import W_DISPLAY_PIX


@dataclass
class CityDrawingData:
    """Drawing data for the poster."""
    theme_colors: CityColors
    title_txt: str
    stats_text: str

    @staticmethod
    def get_stats_items(dist_km_int: int,
                        uphill_m_int: int,
                        duration_s_float: float | None) -> list[str]:
        """Get a list of the items to plot in the stat panel."""
        stats_items = []
        if dist_km_int > 0:
            stats_items.append(f"{dist_km_int} km")
        if uphill_m_int > 0:
            stats_items.append(f"{uphill_m_int} m D+")
        if duration_s_float is not None and duration_s_float > 0:
            stats_items.append(f"{format_timedelta(duration_s_float)}")
        return stats_items

    @staticmethod
    def build_stats_text(stats_items: list[str]) -> str:
        """Transform the stats items list into a string to display."""
        if len(stats_items) == 0:
            return ""
        elif len(stats_items) == 1:
            return stats_items[0]
        elif len(stats_items) == 2:
            return f"{stats_items[0]} - {stats_items[1]}"
        elif len(stats_items) == 3:
            return f"{stats_items[0]} - {stats_items[1]}\n{stats_items[2]}"
        else:
            raise ValueError("The stat items list length is not valid")


@dataclass
class CityDrawer:
    """Class leveraging cache to avoid reprocessing GPX when changing color them, title, stats..."""

    stats_dist_km: float
    stats_uphill_m: float
    stats_duration_s: float | None

    plotter: CityDrawingFigure

    # TODO (upgrade): enhance support for duration with a 2 stats line layout

    @profile
    @staticmethod
    def from_gpx_data(gpx_data: CityAugmentedGpxData,
                      paper_size: PaperSize) -> 'CityDrawer':
        """Create a CityDrawer from a GPX file."""
        layout = CityVerticalLayout.default()

        # Download the elevation map at the correct layout
        img_bounds, paper_fig = layout.get_download_bounds_and_paper_figure(gpx_data.track, paper_size)

        # Use default drawing params
        drawing_size_params = CityLinewidthParams.default(paper_size, img_bounds.diagonal_m)
        drawing_style_params = CityDrawingStyleParams()

        plotter = init_and_populate_drawing_figure(gpx_data, paper_fig, img_bounds, layout, drawing_size_params,
                                                   drawing_style_params)

        logger.info("Successful GPX Processing")

        return CityDrawer(stats_dist_km=gpx_data.dist_km,
                          stats_uphill_m=gpx_data.uphill_m,
                          stats_duration_s=gpx_data.duration_s,
                          plotter=plotter)

    def update_drawing_data(self,
                            colors: CityColors,
                            title_txt: str | None,
                            uphill_m: int | None,
                            duration_s: int | None,
                            dist_km: int | None) -> CityDrawingData:
        """Update the drawing data (can run in a separate thread)."""
        dist_km_int = dist_km if dist_km is not None else self.stats_dist_km
        uphill_m_int = uphill_m if uphill_m is not None else self.stats_uphill_m
        stats_duration_s = duration_s if duration_s is not None else self.stats_duration_s
        stats_text = f"{dist_km_int} km - {uphill_m_int} m D+"

        if title_txt is None:
            title_txt = ""

        if stats_duration_s is not None:
            stats_text += f"\n{format_timedelta(int(stats_duration_s))}"

        new_stats_items = CityDrawingData.get_stats_items(dist_km_int=int(dist_km_int),
                                                          uphill_m_int=int(uphill_m_int),
                                                          duration_s_float=stats_duration_s)

        stats_text = CityDrawingData.build_stats_text(stats_items=new_stats_items)

        return CityDrawingData(theme_colors=colors,
                               title_txt=title_txt,
                               stats_text=stats_text)

    @profile
    def draw(self, fig: Figure, ax: Axes, poster_drawing_data: CityDrawingData) -> None:
        """Draw the updated drawing data (Must run in the main thread because of matplotlib backend)."""
        self.plotter.draw(fig=fig,
                          ax=ax,
                          theme_colors=poster_drawing_data.theme_colors,
                          title_txt=poster_drawing_data.title_txt,
                          stats_txt=poster_drawing_data.stats_text)
        logger.info("Drawing updated")


def init_and_populate_drawing_figure(gpx_data: CityAugmentedGpxData,
                                     base_fig: BaseDrawingFigure,
                                     city_bounds: GpxBounds,
                                     layout: CityVerticalLayout,
                                     drawing_size_params: CityLinewidthParams,
                                     drawing_style_params: CityDrawingStyleParams
                                     ) -> CityDrawingFigure:
    """Set up and populate the DrawingFigure for the poster."""
    gpx_track = gpx_data.track

    caracteristic_distance_m = city_bounds.diagonal_m
    logger.info(f"Domain diagonal is {caracteristic_distance_m/1000.:.1f}km")

    total_query = OverpassQuery()
    for prepare_func in [prepare_download_city_roads,
                         prepare_download_city_rivers,
                         prepare_download_city_forests]:

        prepare_func(query=total_query, bounds=city_bounds)

    # Merge and run all queries
    total_query.launch_queries()

    # Retrieve the data
    roads = process_city_roads(query=total_query,
                               bounds=city_bounds)

    rivers = process_city_rivers(query=total_query,
                                 bounds=city_bounds)

    forests, farmland = process_city_forests(query=total_query,
                                             bounds=city_bounds)
    forests.interior_polygons = []

    track_data: list[BaseDrawingData] = [PlotData(x=gpx_track.list_lon, y=gpx_track.list_lat, linewidth=2.0)]
    road_data: list[BaseDrawingData] = []
    point_data: list[BaseDrawingData] = []
    rivers_data: list[PolygonCollectionData] = [PolygonCollectionData(polygons=rivers)]
    forests_data: list[PolygonCollectionData] = [PolygonCollectionData(polygons=forests)]
    farmland_data: list[PolygonCollectionData] = [PolygonCollectionData(polygons=farmland)]

    for priority, way in roads.items():
        road_data.append(LineCollectionData(way, linewidth=drawing_size_params.linewidth_priority[priority], zorder=1))

    b = base_fig.gpx_bounds
    title = TextData(x=b.lon_center, y=b.lat_max - 0.8 * b.dlat * layout.title_relative_h,
                     s="Title", fontsize=mm_to_point(20.0),
                     fontproperties=drawing_style_params.pretty_font,
                     ha="center",
                     va="center")

    stats_text = f"{gpx_track.list_cumul_dist_km[-1]:.2f} km - {int(gpx_track.uphill_m)} m D+"

    if gpx_track.duration_s is not None:
        stats_text += f"\n{format_timedelta(gpx_track.duration_s)}"

    ele = ElevationStatsSection(layout, base_fig, gpx_track)
    track_data.append(ele.fill_poly)

    stats = TextData(x=b.lon_center, y=b.lat_min + 0.5 * b.dlat * layout.stats_relative_h,
                     s=stats_text, fontsize=mm_to_point(18.5),
                     fontproperties=drawing_style_params.pretty_font,
                     ha="center",
                     va="center")
    point_data.append(ScatterData(x=[gpx_track.list_lon[0]], y=[gpx_track.list_lat[0]],
                                  marker="o", markersize=mm_to_point(3.5)))
    point_data.append(ScatterData(x=[gpx_track.list_lon[-1]], y=[gpx_track.list_lat[-1]],
                                  marker="s", markersize=mm_to_point(3.5)))

    h_top_stats = b.lat_min + b.dlat * layout.stats_relative_h
    track_data.append(PolyFillData(x=[b.lon_min, b.lon_max, b.lon_max, b.lon_min],
                                   y=[h_top_stats, h_top_stats, b.lat_min, b.lat_min]))

    plotter = CityDrawingFigure(paper_size=base_fig.paper_size,
                                latlon_aspect_ratio=base_fig.latlon_aspect_ratio,
                                gpx_bounds=base_fig.gpx_bounds,
                                w_display_pix=W_DISPLAY_PIX,
                                track_data=track_data,
                                road_data=road_data,
                                point_data=point_data,
                                rivers_data=rivers_data,
                                forests_data=forests_data,
                                farmland_data=farmland_data,
                                title=title,
                                stats=stats)

    return plotter
