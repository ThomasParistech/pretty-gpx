#!/usr/bin/python3
"""Overpass Processing."""

from dataclasses import dataclass
from typing import Generic
from typing import TypeVar

import numpy as np
from matplotlib.patches import Polygon
from overpy import Relation
from overpy import RelationRelation
from overpy import RelationWay
from overpy import RelationWayGeometryValue
from overpy import Result
from overpy import Way
from shapely import LineString
from shapely import MultiPolygon as ShapelyMultiPolygon
from shapely import Point as ShapelyPoint
from shapely import Polygon as ShapelyPolygon

from pretty_gpx.common.data.overpass_request import ListLonLat
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.utils import are_close
from pretty_gpx.common.utils.utils import EARTH_RADIUS_M
from pretty_gpx.common.utils.utils import points_are_close


@dataclass(kw_only=True)
class SurfacePolygons:
    """Surface Polygons."""
    exterior_polygons: list[Polygon]
    interior_polygons: list[Polygon]

T = TypeVar('T',bound=list[RelationWayGeometryValue] | ListLonLat)

@dataclass(kw_only=True)
class Segment(Generic[T]):
    """Segment class to use hash tables when merging them."""
    start: tuple[float, float]
    end: tuple[float, float]
    geom: T
    merged: bool

    def __init__(self,
                 start: tuple[float, float],
                 end: tuple[float, float],
                 geom: T) -> None:
        self.start = start
        self.end = end
        self.geom = geom
        self.merged = False





@profile
def get_ways_coordinates_from_results(api_result: Result) -> list[ListLonLat]:
    """Get the lat/lon nodes coordinates of the ways from the overpass API result."""
    ways_coords = []
    for way in api_result.ways:
        road = [(float(node.lon), float(node.lat))
                for node in way.get_nodes(resolve_missing=True)]
        if len(road) > 0:
            ways_coords.append(road)
    # ways_coords = merge_ways(ways_coords)
    return ways_coords



@profile
def get_rivers_polygons_from_lines( api_result: Result,
                                    width: float) -> list[ShapelyPolygon]:
    """Get the rivers center's line into a polygon with a fixed width corresponding to small rivers."""
    ways_coords = []
    for way in api_result.ways:
        if len(way.nodes) <= 2:
            continue
        ways_coords.extend([[(float(node.lon), float(node.lat)) for node in way.nodes 
                             if node.lat is not None and node.lon is not None]])
        new_polygons = []
    for segment in ways_coords:
        line = LineString(segment)
        # Transforms the line into a polygon with 
        # a buffer around the line with half the width
        buffered = line.buffer(width/2.0)
        if isinstance(buffered, ShapelyPolygon):
            #TODO: Check that multipolygons are not useful and can be skiped
            new_polygons.append(buffered)
        elif isinstance(buffered, ShapelyMultiPolygon) and len(buffered) > 0:
            for i in range(len(buffered)):
                polygon = buffered[i]
                new_polygons.append(polygon)
    return new_polygons



@profile
def get_polygons_from_closed_ways(ways_l: list[Way]) -> list[ShapelyPolygon]:
    """Sometimes ways instead of relations are used to describe an area (mainly for rivers)."""
    river_way_polygon = []
    for way in ways_l:
        way_coords = []
        for node in way.get_nodes(resolve_missing=True):
            if node.lat is not None and node.lon is not None:
                way_coords.append((float(node.lon), float(node.lat)))
        if len(way_coords) > 0:
            if way_coords[0][0] == way_coords[-1][0] and way_coords[0][1] == way_coords[-1][1]:
                river_way_polygon.append(ShapelyPolygon(way_coords))
            else:
                logger.warning("Found a shape not closed, skipped")
    return river_way_polygon


def get_polygons_from_relations(results: Result) -> list[ShapelyPolygon]:
    """Get the shapely polygons from the results with all the relations obtained with the Overpass API."""
    polygon_l = []
    relations = results.get_relations()
    for i in range(len(relations)):
        relation_id = relations[i].id
        relation = results.get_relation(rel_id=relation_id, resolve_missing=True)
        polygon_l += get_polygons_from_relation(relation)
    return polygon_l


def get_polygons_from_relation(relation: Relation) -> list[ShapelyPolygon]:
    """Get the polygons from a single relation."""
    polygon_l = []
    relation_members = relation.members
    if relation_members is not None:
        outer_geometry_relation_i: list[list[RelationWayGeometryValue]] = []
        inner_geometry_relation_i: list[list[RelationWayGeometryValue]] = []
        outer_geometry_relation_i, inner_geometry_relation_i = get_members_from_relation(relation)

        #Tolerance is 2m near the point (converted to lon/lat)
        eps = 2/EARTH_RADIUS_M*180/np.pi

        depth_outer = min(max(len(outer_geometry_relation_i)//100,4),4)
        depth_inner = min(max(len(inner_geometry_relation_i)//100,4),4)
        outer_geometry_relation_i = merge_ways_closed_shapes(outer_geometry_relation_i, eps=eps, max_depth=depth_outer)
        inner_geometry_relation_i = merge_ways_closed_shapes(inner_geometry_relation_i, eps=eps, max_depth=depth_inner)

        polygon_l += create_polygons_from_geom(outer_geometry_relation_i, inner_geometry_relation_i)

    return polygon_l


def is_a_closed_shape(geometry: list[RelationWayGeometryValue], eps: float=1e-5) -> bool:
    """Check if a geometry is closed (e.g. last point = first point)."""
    lon_start,lon_end = float(geometry[0].lon),float(geometry[-1].lon)
    lat_start,lat_end = float(geometry[0].lat),float(geometry[-1].lat)
    return are_close(lon_start, lon_end, eps=eps) and are_close(lat_start, lat_end, eps=eps)


def merge_ways_closed_shapes(segments: list[list[RelationWayGeometryValue]],
                             eps: float=1e-3,
                             max_depth: int=2) -> list[list[RelationWayGeometryValue]]:
    """Merge ways until all ways create only closed shape or the max_depth is reached.
    
    This is needed because for closed shapes the algorithm sometimes miss complex/multiple merges
    that occurs at the same point in different direction.
    Or we do not want to complexify the merge way algorithm to have a O(n^2) complexity so to keep
    the O(nlog(n)) complexity in the large majority of cases, we add extra checks only for closed shapes. 
    """
    depth = 0
    all_closed = False

    while depth < max_depth and not all_closed:
        segments = merge_ways(segments, eps=eps)
        all_closed = all(is_a_closed_shape(segment, eps=eps) for segment in segments)
        depth += 1

    if depth > 1:
        logger.info(f"Merging closed shapes used {depth} tries to obtain only closed shapes")

    if not all_closed:
        logger.warning("Despite multiple retries, there are still unclosed exterior geometry")

    return segments



def get_members_from_relation(relation: Relation) -> tuple[list[list[RelationWayGeometryValue]],
                                                                  list[list[RelationWayGeometryValue]]]:
    """Get the members from a relation and classify them by their role."""
    relation_members = relation.members
    if relation_members is not None:
        outer_geometry_l = []
        inner_geometry_l = []
        for member in relation_members:
            if type(member) == RelationRelation:
                logger.debug("Found a RelationRelation i.e. a relation in the members of a relation")
                relation_inside_member = member.resolve(resolve_missing=True)
                outer_subrelation, inner_subrelation = get_members_from_relation(relation_inside_member)
                outer_geometry_l += outer_subrelation
                inner_geometry_l += inner_subrelation
            elif type(member) == RelationWay:
                if member.geometry is None:
                    continue
                if member.role == "outer":
                    outer_geometry_l.append(member.geometry)
                elif member.role == "inner":
                    inner_geometry_l.append(member.geometry)
                else:
                    raise ValueError(f"Unexpected member role in a relation {member.role} not in ['inner','outer']")
            else:
                raise TypeError(
                    f"Unexpected member type {type(member)} not in [RelationWay, RelationRelation]")
    return outer_geometry_l, inner_geometry_l


def hash_point(point: tuple[float, float], eps: float) -> tuple[int, int]:
    """Function to create a hash for points to detect if they are close with a precision of epsilon."""
    return (int(point[0] / eps), int(point[1] / eps))


def get_first_and_last_coords(geom: list[RelationWayGeometryValue] | ListLonLat) -> tuple[tuple[float, float],
                                                                                          tuple[float, float]]:
    """Helper function to extract the first and last coordinates of a geometry."""
    if isinstance(geom[0], RelationWayGeometryValue):
        if not isinstance(geom[-1], RelationWayGeometryValue):
            # This check is only to pass the type checker as we suppose
            # the coherence of types inside the list
            raise TypeError("Unexpected type")
        x_first, y_first = float(geom[0].lat), float(geom[0].lon)
        x_last, y_last = float(geom[-1].lat), float(geom[-1].lon)
    elif isinstance(geom[0], tuple):
        if not isinstance(geom[-1], tuple):
            # This check is only to pass the type checker as we suppose
            # the coherence of types inside the list
            raise TypeError("Unexpected type")
        x_first, y_first = geom[0]
        x_last, y_last = geom[-1]
    else:
        raise TypeError("Unsupported geometry type")
    return (x_first, y_first), (x_last, y_last)



def create_hash_table(segments: list[Segment], eps: float=1e-4) -> dict[tuple[int,int],list[tuple[int,str]]]:
    """Creates a hash table with the start point and the end point using eps as tolerance."""
    point_to_segments: dict[tuple[int,int],list[tuple[int,str]]] = {}
    for i, segment in enumerate(segments):
        start_hash, end_hash = hash_point(segment.start, eps), hash_point(segment.end, eps)
        if start_hash not in point_to_segments:
            point_to_segments[start_hash] = []
        if end_hash not in point_to_segments:
            point_to_segments[end_hash] = []
        point_to_segments[start_hash].append((i, 'start'))
        point_to_segments[end_hash].append((i, 'end'))
    return point_to_segments


def merge_segments_from_hash(segments: list[Segment],
                             hash_table: dict[tuple[int,int],list[tuple[int,str]]],
                             eps: float=1e-4) -> list[T]:
    """Merge the segments localized using the hash table."""
    merged_segments = []
    for i, segment in enumerate(segments):
        if segment.merged:
            continue

        current_segment = segment
        current_segment.merged = True
        merged_geom = current_segment.geom[:]

        while True:
            end_hash = hash_point(current_segment.end, eps)
            found_next = False

            neighbors_hashes = [end_hash,
                                (end_hash[0]-1, end_hash[1]),
                                (end_hash[0]+1, end_hash[1]),
                                (end_hash[0], end_hash[1]-1),
                                (end_hash[0], end_hash[1]+1)]

            for neighbor_hash in neighbors_hashes:
                if neighbor_hash not in hash_table:
                    hash_table[neighbor_hash] = []

                for j, end_type in hash_table[neighbor_hash]:
                    next_segment = segments[j]
                    if next_segment.merged:
                        continue

                    if points_are_close(current_segment.end,
                                        next_segment.start if end_type == 'start' else next_segment.end,
                                        eps=eps):
                        next_segment.merged = True
                        if end_type == 'end':
                            next_segment.geom.reverse()
                        merged_geom.extend(next_segment.geom[1:])
                        current_segment = next_segment
                        found_next = True
                        break

                if found_next:
                    break

            if not found_next:
                break

        merged_segments.append(merged_geom)

    return merged_segments


@profile
def merge_ways(geometry_l: list[T], eps: float = 1e-5) -> list[T]:
    """Merge the connected ways obtained by overpass together."""
    segments_l = [Segment(*get_first_and_last_coords(geom), geom) for geom in geometry_l]
    hash_table = create_hash_table(segments=segments_l,
                                   eps=eps)
    merged_segments: list[T] = merge_segments_from_hash(segments=segments_l,
                                                        hash_table=hash_table,
                                                        eps=eps)
    n_merged = len(geometry_l) - len(merged_segments)
    if n_merged > 0:
        logger.info(f"{n_merged} segments merged")
    return merged_segments



def create_polygons_from_geom(outer_geoms: list[list[RelationWayGeometryValue]],
                              inner_geoms: list[list[RelationWayGeometryValue]]) -> list[ShapelyPolygon]:
    """Create shapely polygons (defined by the exterior shell and the holes) for a single relation."""
    # If multiple outer shells are there, creates multiple polygons instead of a shapely.MultiPolygons
    # Therefore for all relations, the area are described using only ShapelyPolygons
    polygon_l = []
    not_closed = 0
    for outer_geom in outer_geoms:
        point_l = get_lat_lon_from_geometry(outer_geom)
        if len(point_l) <= 4:
            continue
        if point_l[0] != point_l[-1]:
            not_closed += 1
        outer_polygon_i = ShapelyPolygon(point_l)
        holes_i = []
        other_holes = []
        for j in range(len(inner_geoms)):
            member_geom = inner_geoms[j]
            inner_shape_point = ShapelyPoint((float(member_geom[0].lon), float(member_geom[0].lat)))
            if outer_polygon_i.contains(inner_shape_point):
                hole = get_lat_lon_from_geometry(member_geom)
                holes_i.append(hole)
            else:
                other_holes.append(inner_geoms[j])

        polygon_l.append(ShapelyPolygon(shell=point_l,
                                        holes=holes_i))
        inner_geoms = other_holes.copy()
    if len(inner_geoms) > 0:
        logger.warning(f"Could not find an outer for all inner geometries, "
                       f"{len(inner_geoms)} inner geometries are unused")
    if not_closed > 0:
        logger.warning(f"{not_closed} shapes not closed")
    return polygon_l


def get_lat_lon_from_geometry(geom: list[RelationWayGeometryValue]) -> ListLonLat:
    """Returns latitude and longitude points in order to create a shapely shape."""
    point_l = []
    for point in geom:
        point_l.append((float(point.lon), float(point.lat)))
    return point_l


def create_patch_collection_from_polygons(polygons_l: list[ShapelyPolygon]) -> SurfacePolygons:
    """Create a patch list."""
    patches_exterior = []
    patches_interior = []
    for geometry in polygons_l:
        exterior = Polygon(np.array(geometry.exterior.xy).T)
        patches_exterior.append(exterior)
        for i in range(len(geometry.interiors)):
            interior = Polygon(np.array(geometry.interiors[i].xy).T)
            patches_interior.append(interior)
    surface = SurfacePolygons(exterior_polygons=patches_exterior,
                              interior_polygons=patches_interior)
    return surface
