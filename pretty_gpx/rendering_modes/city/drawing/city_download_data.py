#!/usr/bin/python3
"""City Download Data."""
from dataclasses import dataclass

from pretty_gpx.common.data.overpass_processing import SurfacePolygons
from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.drawing.base_drawing_figure import BaseDrawingFigure
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_distance import ListLonLat
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.structure import AugmentedGpxData
from pretty_gpx.common.structure import DownloadData
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.rendering_modes.city.city_vertical_layout import CityVerticalLayout
from pretty_gpx.rendering_modes.city.data.bridges import CityBridge
from pretty_gpx.rendering_modes.city.data.bridges import prepare_download_city_bridges
from pretty_gpx.rendering_modes.city.data.bridges import process_city_bridges
from pretty_gpx.rendering_modes.city.data.city_augmented_gpx_data import CityAugmentedGpxData
from pretty_gpx.rendering_modes.city.data.forests import prepare_download_city_forests
from pretty_gpx.rendering_modes.city.data.forests import process_city_forests
from pretty_gpx.rendering_modes.city.data.rivers import prepare_download_city_rivers
from pretty_gpx.rendering_modes.city.data.rivers import process_city_rivers
from pretty_gpx.rendering_modes.city.data.roads import CityRoadType
from pretty_gpx.rendering_modes.city.data.roads import prepare_download_city_roads
from pretty_gpx.rendering_modes.city.data.roads import process_city_roads


@dataclass
class CityDownloadData(DownloadData):
    """CityDownloadData."""
    bounds: GpxBounds
    layout: CityVerticalLayout
    paper_fig: BaseDrawingFigure
    stats_txt: str

    roads: dict[CityRoadType, list[ListLonLat]]
    rivers: SurfacePolygons
    forests: SurfacePolygons
    farmlands: SurfacePolygons
    bridges: list[CityBridge]

    @staticmethod
    def from_gpx_and_paper_size(gpx_data: AugmentedGpxData, paper: PaperSize) -> 'CityDownloadData':
        """Init the DownloadData from GPX data and Paper Size."""
        from pretty_gpx.rendering_modes.city.drawing.city_drawer import CityDrawingInputs
        assert isinstance(gpx_data, CityAugmentedGpxData)
        stats_items = CityDrawingInputs.get_stats_items(dist_km_int=int(gpx_data.dist_km),
                                                        uphill_m_int=int(gpx_data.uphill_m),
                                                        duration_s_float=gpx_data.duration_s)

        stats_txt, layout = CityDrawingInputs.build_stats_text(stats_items=stats_items)

        download_bounds, paper_fig = layout.get_download_bounds_and_paper_figure(gpx_data.track, paper)

        caracteristic_distance_m = paper_fig.gpx_bounds.diagonal_m
        logger.info(f"Domain diagonal is {caracteristic_distance_m/1000.:.1f}km")

        total_query = OverpassQuery()
        for prepare_func in [prepare_download_city_roads,
                             prepare_download_city_rivers,
                             prepare_download_city_forests]:
            prepare_func(total_query, download_bounds)

        prepare_download_city_bridges(total_query, gpx_data.track)

        # Merge and run all queries
        total_query.launch_queries()

        # Retrieve the data
        roads = process_city_roads(total_query, download_bounds)
        rivers = process_city_rivers(total_query, download_bounds)
        forests, farmlands = process_city_forests(total_query, download_bounds)
        bridges = process_city_bridges(total_query, gpx_data.track)
        forests.interior_polygons = []

        return CityDownloadData(bounds=download_bounds,
                                layout=layout,
                                paper_fig=paper_fig,
                                stats_txt=stats_txt,
                                roads=roads,
                                rivers=rivers,
                                forests=forests,
                                farmlands=farmlands,
                                bridges=bridges)
