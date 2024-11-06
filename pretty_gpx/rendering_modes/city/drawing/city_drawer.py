#!/usr/bin/python3
"""City Drawer."""
from dataclasses import dataclass

from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.drawing.base_drawing_figure import BaseDrawingFigure
from pretty_gpx.common.drawing.drawing_data import BaseDrawingData
from pretty_gpx.common.drawing.drawing_data import LineCollectionData
from pretty_gpx.common.drawing.drawing_data import PlotData
from pretty_gpx.common.drawing.drawing_data import PolygonCollectionData
from pretty_gpx.common.drawing.drawing_data import ScatterData
from pretty_gpx.common.drawing.drawing_data import TextData
from pretty_gpx.common.drawing.elevation_stats_section import ElevationStatsSection
from pretty_gpx.common.drawing.fonts import FontEnum
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.structure import Drawer
from pretty_gpx.common.structure import DrawingInputs
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
from pretty_gpx.rendering_modes.city.drawing.city_drawing_config import CityDrawingSizeConfig
from pretty_gpx.rendering_modes.city.drawing.city_drawing_config import CityDrawingStyleConfig
from pretty_gpx.rendering_modes.city.drawing.city_drawing_figure import CityDrawingFigure
from pretty_gpx.rendering_modes.city.drawing.city_drawing_figure import CityDrawingParams


@dataclass(frozen=True)
class CityDrawingInputs(DrawingInputs):
    """Input Data to be transformed into CityDrawingParams."""
    theme_colors: CityColors
    title_txt: str | None
    uphill_m: int | None
    duration_s: int | None
    dist_km: float | None

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
    def build_stats_text(stats_items: list[str]) -> tuple[str, CityVerticalLayout]:
        """Transform the stats items list into a string to display."""
        if len(stats_items) == 0:
            return "", CityVerticalLayout.single_line_stats()
        elif len(stats_items) == 1:
            return stats_items[0], CityVerticalLayout.single_line_stats()
        elif len(stats_items) == 2:
            return f"{stats_items[0]} - {stats_items[1]}", CityVerticalLayout.single_line_stats()
        elif len(stats_items) == 3:
            return f"{stats_items[0]} - {stats_items[1]}\n{stats_items[2]}", CityVerticalLayout.two_lines_stats()
        else:
            raise ValueError("The stat items list length is not valid")


@dataclass
class CityDrawer(Drawer[CityAugmentedGpxData,
                        CityDrawingInputs,
                        CityDrawingParams]):
    """Class leveraging cache to avoid reprocessing GPX when changing color them, title, stats..."""

    stats_dist_km: float
    stats_uphill_m: float
    stats_duration_s: float | None

    @staticmethod
    def get_gpx_data_cls() -> type[CityAugmentedGpxData]:
        """Return the template AugmentedGpxData class (Because Python doesn't allow to use T as a type)."""
        return CityAugmentedGpxData

    @profile
    @staticmethod
    def from_gpx_data(gpx_data: CityAugmentedGpxData,
                      paper_size: PaperSize) -> 'CityDrawer':
        """Create a CityDrawer from a GPX file."""
        stats_items = CityDrawingInputs.get_stats_items(dist_km_int=int(gpx_data.dist_km),
                                                        uphill_m_int=int(gpx_data.uphill_m),
                                                        duration_s_float=gpx_data.duration_s)

        stats_txt, layout = CityDrawingInputs.build_stats_text(stats_items=stats_items)

        # Download the elevation map at the correct layout
        download_bounds, paper_fig = layout.get_download_bounds_and_paper_figure(gpx_data.track, paper_size)

        # Use default drawing params
        drawing_size_config = CityDrawingSizeConfig.default(paper_size, paper_fig.gpx_bounds.diagonal_m)
        drawing_style_config = CityDrawingStyleConfig()

        plotter = init_and_populate_drawing_figure(gpx_data=gpx_data,
                                                   base_fig=paper_fig,
                                                   download_bounds=download_bounds,
                                                   layout=layout,
                                                   stats_text=stats_txt,
                                                   drawing_size_config=drawing_size_config,
                                                   drawing_style_config=drawing_style_config)

        logger.info("Successful GPX Processing")

        return CityDrawer(stats_dist_km=gpx_data.dist_km,
                          stats_uphill_m=gpx_data.uphill_m,
                          stats_duration_s=gpx_data.duration_s,
                          plotter=plotter,
                          gpx_data=gpx_data)

    @profile
    def get_params(self, inputs: CityDrawingInputs) -> CityDrawingParams:
        """Convert DrawingInputs to DrawingParams."""
        dist_km_int = inputs.dist_km if inputs.dist_km is not None else self.stats_dist_km
        uphill_m_int = inputs.uphill_m if inputs.uphill_m is not None else self.stats_uphill_m
        stats_duration_s = inputs.duration_s if inputs.duration_s is not None else self.stats_duration_s
        stats_text = f"{dist_km_int} km - {uphill_m_int} m D+"

        title_txt = inputs.title_txt if inputs.title_txt is not None else ""

        if stats_duration_s is not None:
            stats_text += f"\n{format_timedelta(int(stats_duration_s))}"

        new_stats_items = CityDrawingInputs.get_stats_items(dist_km_int=int(dist_km_int),
                                                            uphill_m_int=int(uphill_m_int),
                                                            duration_s_float=stats_duration_s)

        stats_text, layout = CityDrawingInputs.build_stats_text(stats_items=new_stats_items)

        return CityDrawingParams(theme_colors=inputs.theme_colors,
                                 title_txt=title_txt,
                                 stats_txt=stats_text,
                                 layout=layout)


def init_and_populate_drawing_figure(gpx_data: CityAugmentedGpxData,
                                     base_fig: BaseDrawingFigure,
                                     download_bounds: GpxBounds,
                                     layout: CityVerticalLayout,
                                     stats_text: str,
                                     drawing_size_config: CityDrawingSizeConfig,
                                     drawing_style_config: CityDrawingStyleConfig
                                     ) -> CityDrawingFigure:
    """Set up and populate the DrawingFigure for the poster."""
    gpx_track = gpx_data.track

    caracteristic_distance_m = base_fig.gpx_bounds.diagonal_m
    logger.info(f"Domain diagonal is {caracteristic_distance_m/1000.:.1f}km")

    total_query = OverpassQuery()
    for prepare_func in [prepare_download_city_roads,
                         prepare_download_city_rivers,
                         prepare_download_city_forests]:

        prepare_func(query=total_query, bounds=download_bounds)

    # Merge and run all queries
    total_query.launch_queries()

    # Retrieve the data
    roads = process_city_roads(query=total_query,
                               bounds=download_bounds)

    rivers = process_city_rivers(query=total_query,
                                 bounds=download_bounds)

    forests, farmland = process_city_forests(query=total_query,
                                             bounds=download_bounds)
    forests.interior_polygons = []

    track_data: list[BaseDrawingData] = [PlotData(x=gpx_track.list_lon, y=gpx_track.list_lat, linewidth=2.0)]
    road_data: list[BaseDrawingData] = []
    point_data: list[BaseDrawingData] = []
    rivers_data: list[PolygonCollectionData] = [PolygonCollectionData(polygons=rivers)]
    forests_data: list[PolygonCollectionData] = [PolygonCollectionData(polygons=forests)]
    farmland_data: list[PolygonCollectionData] = [PolygonCollectionData(polygons=farmland)]

    for priority, way in roads.items():
        road_data.append(LineCollectionData(way, linewidth=drawing_size_config.linewidth_priority[priority], zorder=1))

    b = base_fig.gpx_bounds
    title = TextData(x=b.lon_center, y=b.lat_max - 0.8 * b.dlat * layout.title_relative_h,
                     s="Title", fontsize=mm_to_point(20.0),
                     fontproperties=FontEnum.TITLE.value,
                     ha="center",
                     va="center")

    elevation_profile = ElevationStatsSection(layout, base_fig, gpx_track)

    stats = TextData(x=b.lon_center, y=b.lat_min + 0.5 * b.dlat * layout.stats_relative_h,
                     s=stats_text, fontsize=mm_to_point(18.5),
                     fontproperties=FontEnum.STATS.value,
                     ha="center",
                     va="center")
    point_data.append(ScatterData(x=[gpx_track.list_lon[0]], y=[gpx_track.list_lat[0]],
                                  marker="o", markersize=mm_to_point(3.5)))
    point_data.append(ScatterData(x=[gpx_track.list_lon[-1]], y=[gpx_track.list_lat[-1]],
                                  marker="s", markersize=mm_to_point(3.5)))

    plotter = CityDrawingFigure(paper_size=base_fig.paper_size,
                                latlon_aspect_ratio=base_fig.latlon_aspect_ratio,
                                gpx_bounds=base_fig.gpx_bounds,
                                track_data=track_data,
                                road_data=road_data,
                                point_data=point_data,
                                rivers_data=rivers_data,
                                forests_data=forests_data,
                                farmland_data=farmland_data,
                                elevation_profile=elevation_profile,
                                title=title,
                                stats=stats)

    return plotter
