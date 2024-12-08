#!/usr/bin/python3
"""City Drawer."""
from dataclasses import dataclass

import numpy as np

from pretty_gpx.common.drawing.drawing_data import BaseDrawingData
from pretty_gpx.common.drawing.drawing_data import LineCollectionData
from pretty_gpx.common.drawing.drawing_data import PlotData
from pretty_gpx.common.drawing.drawing_data import PolygonCollectionData
from pretty_gpx.common.drawing.drawing_data import ScatterData
from pretty_gpx.common.drawing.drawing_data import TextData
from pretty_gpx.common.drawing.elevation_stats_section import ElevationStatsSection
from pretty_gpx.common.drawing.fonts import FontEnum
from pretty_gpx.common.drawing.text_allocation import allocate_text
from pretty_gpx.common.drawing.text_allocation import AnnotatedScatterDataCollection
from pretty_gpx.common.structure import Drawer
from pretty_gpx.common.structure import DrawingInputs
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.utils import format_timedelta
from pretty_gpx.common.utils.utils import mm_to_point
from pretty_gpx.rendering_modes.city.city_vertical_layout import CityVerticalLayout
from pretty_gpx.rendering_modes.city.data.bridges import CityBridge
from pretty_gpx.rendering_modes.city.data.city_augmented_gpx_data import CityAugmentedGpxData
from pretty_gpx.rendering_modes.city.drawing.city_colors import CityColors
from pretty_gpx.rendering_modes.city.drawing.city_download_data import CityDownloadData
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
                        CityDownloadData,
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

    @staticmethod
    def get_download_data_cls() -> type[CityDownloadData]:
        """Return the template CityDownloadData class (Because Python doesn't allow to use U as a type)."""
        return CityDownloadData

    @profile
    @staticmethod
    def from_gpx_and_download_data(gpx_data: CityAugmentedGpxData, download_data: CityDownloadData) -> 'CityDrawer':
        """Create a CityDrawer from a GPX file."""
        # Use default drawing params
        drawing_size_config = CityDrawingSizeConfig.default(download_data.paper_fig.paper_size,
                                                            download_data.paper_fig.gpx_bounds.diagonal_m)

        drawing_style_config = CityDrawingStyleConfig()

        plotter = init_and_populate_drawing_figure(gpx_data=gpx_data,
                                                   download_data=download_data,
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
                                     download_data: CityDownloadData,
                                     drawing_size_config: CityDrawingSizeConfig,
                                     drawing_style_config: CityDrawingStyleConfig) -> CityDrawingFigure:
    """Set up and populate the DrawingFigure for the poster."""
    gpx_track = gpx_data.track

    track_data: list[BaseDrawingData] = [PlotData(x=gpx_track.list_lon, y=gpx_track.list_lat, linewidth=2.0)]
    road_data: list[BaseDrawingData] = []
    point_data: list[BaseDrawingData] = []
    rivers_data: list[PolygonCollectionData] = [PolygonCollectionData(polygons=download_data.rivers)]
    forests_data: list[PolygonCollectionData] = [PolygonCollectionData(polygons=download_data.forests)]
    farmland_data: list[PolygonCollectionData] = [PolygonCollectionData(polygons=download_data.farmlands)]
    bridges_l: list[CityBridge] = download_data.bridges

    for priority, way in download_data.roads.items():
        road_data.append(LineCollectionData(way, linewidth=drawing_size_config.linewidth_priority[priority], zorder=1))

    b = download_data.paper_fig.gpx_bounds
    title = TextData(x=b.lon_center, y=b.lat_max - 0.8 * b.dlat * download_data.layout.title_relative_h,
                     s="Title", fontsize=mm_to_point(20.0),
                     fontproperties=FontEnum.TITLE.value,
                     ha="center",
                     va="center")

    elevation_profile = ElevationStatsSection(download_data.layout, download_data.paper_fig, gpx_track)

    stats = TextData(x=b.lon_center, y=b.lat_min + 0.5 * b.dlat * download_data.layout.stats_relative_h,
                     s=download_data.stats_txt, fontsize=mm_to_point(18.5),
                     fontproperties=FontEnum.STATS.value,
                     ha="center",
                     va="center")
    point_data.append(ScatterData(x=[gpx_track.list_lon[0]], y=[gpx_track.list_lat[0]],
                                  marker="o", markersize=mm_to_point(3.5)))
    point_data.append(ScatterData(x=[gpx_track.list_lon[-1]], y=[gpx_track.list_lat[-1]],
                                  marker="s", markersize=mm_to_point(3.5)))

    scatters = init_annotated_scatter_collection(city_bridges=bridges_l,
                                                 drawing_style_config=drawing_style_config,
                                                 drawing_size_config=drawing_size_config)

    plots_x_to_avoid, plots_y_to_avoid = [gpx_track.list_lon], [gpx_track.list_lat]

    for y in b.lat_min+b.dlat*np.concatenate((np.linspace(0., download_data.layout.stats_relative_h + 
                                                          download_data.layout.elevation_relative_h,
                                                          num=10, endpoint=True),  # Stats+Elevation area
                                              np.linspace(1.0-download_data.layout.title_relative_h, 1.0,
                                                          num=10, endpoint=True))):  # Title area
        plots_x_to_avoid.append([b.lon_min, b.lon_max])
        plots_y_to_avoid.append([y, y])

    texts, arrows = allocate_text(base_fig=download_data.paper_fig,
                                  scatters=scatters,
                                  plots_x_to_avoid=plots_x_to_avoid,
                                  plots_y_to_avoid=plots_y_to_avoid,
                                  output_linewidth=drawing_size_config.text_arrow_linewidth,
                                  fontsize=drawing_size_config.text_fontsize,
                                  fontproperties=FontEnum.ANNOTATION.value)

    bridges_data: list[BaseDrawingData] =  texts + arrows + scatters.list_scatter_data  # type:ignore

    plotter = CityDrawingFigure(paper_size=download_data.paper_fig.paper_size,
                                latlon_aspect_ratio=download_data.paper_fig.latlon_aspect_ratio,
                                gpx_bounds=download_data.paper_fig.gpx_bounds,
                                track_data=track_data,
                                road_data=road_data,
                                point_data=point_data,
                                rivers_data=rivers_data,
                                forests_data=forests_data,
                                farmland_data=farmland_data,
                                bridges_data=bridges_data,
                                elevation_profile=elevation_profile,
                                title=title,
                                stats=stats)

    return plotter


def init_annotated_scatter_collection(city_bridges: list[CityBridge],
                                      drawing_style_config: CityDrawingStyleConfig,
                                      drawing_size_config: CityDrawingSizeConfig) -> AnnotatedScatterDataCollection:
    """Initialize the AnnotatedScatterDataCollection with the mountain passes, huts, start and end markers."""
    scatter_collection = AnnotatedScatterDataCollection()
    list_x_bridges = []
    list_y_bridges = []
    list_name_bridges = []
    for bridge in city_bridges:
        list_x_bridges.append(bridge.lon)
        list_y_bridges.append(bridge.lat)
        list_name_bridges.append(bridge.name)
    ids = list(range(len(list_name_bridges)))


    scatter_collection.add_scatter_data(global_x=list_x_bridges,
                                        global_y=list_y_bridges,
                                        scatter_ids=ids,
                                        scatter_texts=list_name_bridges,
                                        marker=drawing_style_config.bridge_marker,
                                        markersize=drawing_size_config.bridge_markersize)

    return scatter_collection