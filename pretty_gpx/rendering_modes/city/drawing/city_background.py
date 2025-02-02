#!/usr/bin/python3
"""Drawing Component for a City Background."""
from dataclasses import dataclass
from typing import Protocol

from pretty_gpx.common.drawing.utils.drawing_figure import DrawingFigure
from pretty_gpx.common.drawing.utils.drawing_figure import MetersFloat
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_distance import ListLonLat
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.request.overpass_processing import SurfacePolygons
from pretty_gpx.common.request.overpass_request import OverpassQuery
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.utils import safe
from pretty_gpx.rendering_modes.city.data.forests import prepare_download_city_forests
from pretty_gpx.rendering_modes.city.data.forests import process_city_forests
from pretty_gpx.rendering_modes.city.data.rivers import prepare_download_city_rivers
from pretty_gpx.rendering_modes.city.data.rivers import process_city_rivers
from pretty_gpx.rendering_modes.city.data.roads import CityRoadPrecision
from pretty_gpx.rendering_modes.city.data.roads import CityRoadType
from pretty_gpx.rendering_modes.city.data.roads import prepare_download_city_roads
from pretty_gpx.rendering_modes.city.data.roads import process_city_roads


class CityBackgroundParamsProtocol(Protocol):
    """Protocol for City Background Parameters."""
    @property
    def city_roads_lw(self) -> dict[CityRoadType, MetersFloat]: ...  # noqa: D102

    city_dark_mode: bool
    city_background_color: str
    city_farmland_color: str
    city_rivers_color: str
    city_forests_color: str


@dataclass(kw_only=True)
class CityBackground:
    """Drawing Component for a City Background."""
    union_bounds: GpxBounds

    full_roads: dict[CityRoadType, list[ListLonLat]]
    full_rivers: SurfacePolygons
    full_forests: SurfacePolygons
    full_farmlands: SurfacePolygons

    paper_roads: dict[CityRoadType, list[ListLonLat]] | None
    paper_rivers: SurfacePolygons | None
    paper_forests: SurfacePolygons | None
    paper_farmlands: SurfacePolygons | None

    @staticmethod
    @profile
    def from_union_bounds(union_bounds: GpxBounds,
                          road_precision: CityRoadPrecision) -> 'CityBackground':
        """Initialize the City Background from the Union Bounds."""
        total_query = OverpassQuery()
        roads_downloaded = prepare_download_city_roads(total_query, union_bounds, road_precision)
        prepare_download_city_rivers(total_query, union_bounds)
        prepare_download_city_forests(total_query, union_bounds)

        total_query.launch_queries()

        # Retrieve the data
        roads = process_city_roads(total_query, union_bounds, roads_downloaded, road_precision)
        rivers = process_city_rivers(total_query, union_bounds)
        forests, farmlands = process_city_forests(total_query, union_bounds)
        forests.interior_polygons = []

        return CityBackground(union_bounds=union_bounds,
                              full_roads=roads, full_rivers=rivers, full_forests=forests, full_farmlands=farmlands,
                              paper_roads=None, paper_rivers=None, paper_forests=None, paper_farmlands=None)

    @profile
    def change_papersize(self, paper: PaperSize, bounds: GpxBounds) -> None:
        """Change Paper Size and GPX Bounds."""
        # TODO(upgrade): Change the paper size. For now, just copy the full data and let the plot hide the rest
        self.paper_roads = self.full_roads
        self.paper_rivers = self.full_rivers
        self.paper_forests = self.full_forests
        self.paper_farmlands = self.full_farmlands

    @profile
    def draw(self, fig: DrawingFigure, params: CityBackgroundParamsProtocol) -> None:
        """Draw the farmlands, forests, rivers and roads."""
        fig.polygon_collection(lon_lat_polygons=safe(self.paper_farmlands),
                               color_patch=params.city_farmland_color,
                               color_background=params.city_background_color)
        fig.polygon_collection(lon_lat_polygons=safe(self.paper_forests),
                               color_patch=params.city_forests_color,
                               color_background=params.city_farmland_color)
        fig.polygon_collection(lon_lat_polygons=safe(self.paper_rivers),
                               color_patch=params.city_rivers_color,
                               color_background=params.city_background_color)

        road_color = "black" if params.city_dark_mode else "white"
        for priority, roads in safe(self.paper_roads).items():
            fig.line_collection(lon_lat_lines=roads,
                                lw=params.city_roads_lw[priority],
                                color=road_color)

        fig.background_color(params.city_background_color)
