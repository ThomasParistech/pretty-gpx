#!/usr/bin/python3
"""Drawing Component for a City Background."""
from dataclasses import dataclass
from typing import Protocol

from shapely import Point as ShapelyPoint
from shapely import Polygon as ShapelyPolygon

from pretty_gpx.common.drawing.utils.drawing_figure import DrawingFigure
from pretty_gpx.common.drawing.utils.drawing_figure import MetersFloat
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_distance import ListLonLat
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.request.overpass_processing import SurfacePolygons
from pretty_gpx.common.request.overpass_request import OverpassQuery
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.common.utils.utils import safe
from pretty_gpx.rendering_modes.city.data.forests import prepare_download_city_forests
from pretty_gpx.rendering_modes.city.data.forests import process_city_forests
from pretty_gpx.rendering_modes.city.data.rivers import prepare_download_city_rivers
from pretty_gpx.rendering_modes.city.data.rivers import process_city_rivers
from pretty_gpx.rendering_modes.city.data.roads import CityRoadPrecision
from pretty_gpx.rendering_modes.city.data.roads import prepare_download_city_roads
from pretty_gpx.rendering_modes.city.data.roads import process_city_roads


class CityBackgroundParamsProtocol(Protocol):
    """Protocol for City Background Parameters."""
    @property
    def city_roads_lw(self) -> dict[CityRoadPrecision, MetersFloat]: ...  # noqa: D102

    city_road_max_precision: CityRoadPrecision
    city_dark_mode: bool
    city_background_color: str
    city_farmland_color: str
    city_rivers_color: str
    city_forests_color: str


@dataclass(kw_only=True)
class CityBackground:
    """Drawing Component for a City Background."""
    union_bounds: GpxBounds

    full_roads: dict[CityRoadPrecision, list[ListLonLat]]
    full_rivers: SurfacePolygons
    full_forests: SurfacePolygons
    full_farmlands: SurfacePolygons

    paper_roads: dict[CityRoadPrecision, list[ListLonLat]] | None
    paper_rivers: SurfacePolygons | None
    paper_forests: SurfacePolygons | None
    paper_farmlands: SurfacePolygons | None

    @staticmethod
    @profile
    def from_union_bounds(union_bounds: GpxBounds) -> 'CityBackground':
        """Initialize the City Background from the Union Bounds."""
        total_query = OverpassQuery()
        prepare_download_city_roads(total_query, union_bounds)
        prepare_download_city_rivers(total_query, union_bounds)
        prepare_download_city_forests(total_query, union_bounds)

        total_query.launch_queries()

        # Retrieve the data
        roads = process_city_roads(total_query, union_bounds)
        rivers = process_city_rivers(total_query, union_bounds)
        forests, farmlands = process_city_forests(total_query, union_bounds)
        forests.interior_polygons = []

        return CityBackground(union_bounds=union_bounds,
                              full_roads=roads, full_rivers=rivers, full_forests=forests, full_farmlands=farmlands,
                              paper_roads=None, paper_rivers=None, paper_forests=None, paper_farmlands=None)

    @staticmethod
    @profile
    def surface_polygons_inside_bounds(surface_polygons: SurfacePolygons, bounds: GpxBounds) -> SurfacePolygons:
        """Get the surface polygons inside the drawing bounds."""
        lat_min, lat_max, lon_min, lon_max = bounds.lat_min, bounds.lat_max, bounds.lon_min, bounds.lon_max
        rectangle = ShapelyPolygon([(lon_min, lat_min), (lon_max, lat_min), (lon_max, lat_max), (lon_min, lat_max)])
        inner_polygons_inside = [polygon for polygon in surface_polygons.interior_polygons 
                                 if not rectangle.disjoint(ShapelyPolygon(polygon.get_xy()[:-1]))]
        outer_polygons_inside = [polygon for polygon in surface_polygons.exterior_polygons 
                                 if not rectangle.disjoint(ShapelyPolygon(polygon.get_xy()[:-1]))]
        polygons_inside = SurfacePolygons(exterior_polygons=outer_polygons_inside,
                                          interior_polygons=inner_polygons_inside)
        return polygons_inside

    @staticmethod
    @profile
    def roads_inside_bounds(city_roads: dict[CityRoadType, list[ListLonLat]],
                            bounds: GpxBounds) -> dict[CityRoadType, list[ListLonLat]]:
        """Get the roads inside the drawing bounds."""
        lat_min, lat_max, lon_min, lon_max = bounds.lat_min, bounds.lat_max, bounds.lon_min, bounds.lon_max
        rectangle = ShapelyPolygon([(lon_min, lat_min), (lon_max, lat_min), (lon_max, lat_max), (lon_min, lat_max)])
        city_roads_inside: dict[CityRoadType, list[ListLonLat]] = dict()
        for city_road_type, roads_l in city_roads.items():
            city_roads_inside[city_road_type] = []
            for road in roads_l:
                first_point = ShapelyPoint(road[0])
                last_point = ShapelyPoint(road[-1])

                first_point_inside = rectangle.contains(first_point)
                last_point_inside = rectangle.contains(last_point)

                if first_point_inside or last_point_inside:
                    city_roads_inside[city_road_type].append(road)
        return city_roads_inside

    @profile
    def change_papersize(self, paper: PaperSize, bounds: GpxBounds) -> None:
        """Change Paper Size and GPX Bounds."""
        # TODO(upgrade): Change the paper size. For now, just copy the full data and let the plot hide the rest
        with Profiling.Scope("CHANGE PAPERSIZE"):
            self.paper_roads = CityBackground.roads_inside_bounds(self.full_roads, bounds=bounds)
            self.paper_rivers = CityBackground.surface_polygons_inside_bounds(self.full_rivers, bounds=bounds)
            self.paper_forests = CityBackground.surface_polygons_inside_bounds(self.full_forests, bounds=bounds)
            self.paper_farmlands = CityBackground.surface_polygons_inside_bounds(self.full_farmlands, bounds=bounds)

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
        for road_precision in CityRoadPrecision:  # Filter roads by precision
            if road_precision <= params.city_road_max_precision:
                fig.line_collection(lon_lat_lines=safe(self.paper_roads)[road_precision],
                                    lw=params.city_roads_lw[road_precision],
                                    color=road_color)

        fig.background_color(params.city_background_color)
