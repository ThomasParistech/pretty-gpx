#!/usr/bin/python3
"""Bridges."""
import os
from dataclasses import dataclass

import numpy as np
from overpy import Relation
from overpy import RelationWay
from overpy import Way
from shapely import oriented_envelope
from shapely.geometry import GeometryCollection
from shapely.geometry import LineString
from shapely.geometry import MultiLineString
from shapely.geometry import Point
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry.base import BaseGeometry

from pretty_gpx.common.drawing.utils.scatter_point import ScatterPoint
from pretty_gpx.common.drawing.utils.scatter_point import ScatterPointCategory
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.request.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.request.osm_name import get_shortest_name
from pretty_gpx.common.request.overpass_processing import get_lat_lon_from_geometry
from pretty_gpx.common.request.overpass_processing import get_way_coordinates
from pretty_gpx.common.request.overpass_processing import merge_ways
from pretty_gpx.common.request.overpass_request import OverpassQuery
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.common.utils.utils import EARTH_RADIUS_M

BRIDGES_CACHE = GpxDataCacheHandler(name='bridges', extension='.pkl')

BRIDGES_RELATIONS_ARRAY_NAME = "bridges_relations"
BRIDGES_WAYS_ARRAY_NAME = "bridges_ways"


@dataclass
class Bridge:
    """Bridge."""
    name: str | None
    polygon: ShapelyPolygon
    length: float
    aspect_ratio: float
    center: Point


class BridgeApproximation:
    """Bridge rectangle approximation."""
    MAXIMUM_BRIDGE_ASPECT_RATIO = 0.75
    MINIMUM_BRIDGE_ASPECT_RATIO = 0.1
    MIN_BRIDGE_LENGTH_M = 40
    MIN_BRIDGE_LENGTH = np.rad2deg(MIN_BRIDGE_LENGTH_M/EARTH_RADIUS_M)

    @staticmethod
    def get_minimum_rectangle(polygon: ShapelyPolygon,
                              min_aspect_ratio: float = MINIMUM_BRIDGE_ASPECT_RATIO,
                              min_length: float = MIN_BRIDGE_LENGTH) -> tuple[ShapelyPolygon | None, float, float]:
        """Adjusts an oriented rectangle to meet a minimum aspect ratio by enlarging its width if necessary.

        Args:
            polygon: The shapely polygon of the bridge
            min_aspect_ratio: The minimum allowed aspect ratio (width/length), defaults to 0.1
            min_length: Minimum bridge length

        Returns the adjusted rectangle as a Shapely Polygon, the final aspect ratio, the bridge length
        """
        if polygon.is_empty or polygon.area == 0:
            raise ValueError("Input polygon is empty or degenerate.")

        min_rot_rect = oriented_envelope(polygon)
        if not hasattr(min_rot_rect, "exterior"):
            raise ValueError("The minimum rotated rectangle does not have an exterior.")

        rectangle = ShapelyPolygon(np.array(min_rot_rect.exterior.coords)) # type: ignore
        coords = list(rectangle.exterior.coords[:-1])
        sides = [(np.linalg.norm(np.array(coords[i]) - np.array(coords[(i + 1) % 4])),
                  LineString([coords[i], coords[(i + 1) % 4]])) for i in range(4)]
        sides.sort(key=lambda x: float(x[0]), reverse=True)
        longest_length, shortest_length = float(sides[0][0]), float(sides[3][0])
        aspect_ratio = shortest_length / longest_length

        if (sides[0][0] + sides[1][0])/2.0 < min_length:
            logger.warning("Bridge has not minimum length")
            return None, 0., 0.

        if aspect_ratio >= min_aspect_ratio:
            return rectangle, aspect_ratio, longest_length

        p1, p2 = sides[2][1].interpolate(0.5, normalized=True), sides[3][1].interpolate(0.5, normalized=True)
        median_line = LineString([p1, p2])
        buffer_size = float(longest_length * min_aspect_ratio) / 2.

        return ShapelyPolygon(median_line.buffer(buffer_size)), min_aspect_ratio, longest_length

    @classmethod
    def create_bridge(cls, way_or_relation: Way | Relation) -> Bridge | None:
        """Create a Bridge object from a way."""
        try:
            if isinstance(way_or_relation, Way):
                bridge_coords = get_way_coordinates(way_or_relation)
            elif isinstance(way_or_relation, Relation) and way_or_relation.members is not None:
                outer_members = [
                    member.geometry for member in way_or_relation.members
                    if type(member) == RelationWay and member.geometry is not None and member.role == "outer"]

                merged_ways = merge_ways(outer_members)
                if len(merged_ways) > 1:
                    logger.error("Multiple geometries found")
                    return None
                bridge_coords = get_lat_lon_from_geometry(merged_ways[0])
            else:
                raise TypeError   

            bridge_polygon = ShapelyPolygon(bridge_coords)
            bridge_simplified, aspect_ratio, longest_length = cls.get_minimum_rectangle(bridge_polygon)
            bridge_name = get_shortest_name(way_or_relation)

            if not bridge_simplified or aspect_ratio > cls.MAXIMUM_BRIDGE_ASPECT_RATIO:
                logger.warning(f"Skipped bridge {bridge_name}: invalid aspect ratio or length.")
                return None

            return Bridge(name=bridge_name,
                          polygon=bridge_simplified,
                          length=longest_length,
                          aspect_ratio=aspect_ratio,
                          center=bridge_polygon.centroid)
        except Exception as e:
            logger.error(f"Error processing bridge: {e}")
            return None

class BridgeCrossingAnalyzer:
    """Bridge and track intersection."""
    INTERSECTION_THRESHOLD = 0.75

    @staticmethod
    def analyze_track_bridge_crossing(track: GpxTrack, bridges: list[Bridge]) -> list[Bridge]:
        """Returns bridges significantly crossed by the track."""
        crossed_bridges = []
        shapely_track = LineString(list(zip(track.list_lon, track.list_lat)))

        for bridge in bridges:
            intersection = shapely_track.intersection(bridge.polygon)
            if not intersection.is_empty:
                intersection_length = BridgeCrossingAnalyzer._calculate_length(intersection)
                if intersection_length > BridgeCrossingAnalyzer.INTERSECTION_THRESHOLD * bridge.length:
                    logger.debug(f"{bridge.name} crossed")
                    crossed_bridges.append(bridge)
        return crossed_bridges

    @staticmethod
    def _calculate_length(geometry: BaseGeometry) -> float:
        """Calculate total length of intersection geometry."""
        if isinstance(geometry, GeometryCollection | MultiLineString):
            return sum(geom.length for geom in geometry.geoms if isinstance(geom, LineString))
        return geometry.length if isinstance(geometry, LineString) else 0

@profile
def prepare_download_city_bridges(query: OverpassQuery, track: GpxTrack) -> None:
    """Add the queries for city bridges inside the global OverpassQuery."""
    cache_pkl = BRIDGES_CACHE.get_path(track)
    if os.path.isfile(cache_pkl):
        query.add_cached_result(BRIDGES_CACHE.name, cache_file=cache_pkl)
        return

    query.add_around_ways_overpass_query(array_name=BRIDGES_WAYS_ARRAY_NAME,
                                         query_elements=['way["name"]["wikidata"]["man_made"="bridge"]'],
                                         gpx_track=track,
                                         relations=False,
                                         radius_m=40)

    query.add_around_ways_overpass_query(array_name=BRIDGES_RELATIONS_ARRAY_NAME,
                                         query_elements=['relation["name"]["wikidata"]["man_made"="bridge"]'],
                                         gpx_track=track,
                                         relations=True,
                                         radius_m=40)

@profile
def process_city_bridges(query: OverpassQuery, track: GpxTrack) -> list[ScatterPoint]:
    """Process the overpass API result to get the bridges of a city."""
    if query.is_cached(BRIDGES_CACHE.name):
        return read_pickle(query.get_cache_file(BRIDGES_CACHE.name))

    with Profiling.Scope("Process Bridges"):
        bridges = [BridgeApproximation.create_bridge(way)
                   for way in query.get_query_result(BRIDGES_WAYS_ARRAY_NAME).ways]
        bridges += [BridgeApproximation.create_bridge(rel)
                    for rel in query.get_query_result(BRIDGES_RELATIONS_ARRAY_NAME).relations]
        crossed_bridges = BridgeCrossingAnalyzer.analyze_track_bridge_crossing(track, [b for b in bridges if b])
        result = [ScatterPoint(name=b.name, lat=b.center.y, lon=b.center.x, category=ScatterPointCategory.CITY_BRIDGE)
                  for b in crossed_bridges]

    logger.info(f"Found {len(result)} bridge(s)")
    write_pickle(BRIDGES_CACHE.get_path(track), result)
    query.add_cached_result(BRIDGES_CACHE.name, cache_file=BRIDGES_CACHE.get_path(track))
    return result