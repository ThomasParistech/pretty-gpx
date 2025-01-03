#!/usr/bin/python3
"""Overpass Processing."""
from dataclasses import dataclass
from typing import cast
from typing import Generic
from typing import TypeVar

import numpy as np
from matplotlib.patches import Polygon
from overpy import Relation
from overpy import RelationNode
from overpy import RelationRelation
from overpy import RelationWay
from overpy import RelationWayGeometryValue
from overpy import Result
from overpy import Way
from shapely import LinearRing as ShapelyLinearRing
from shapely import LineString
from shapely import MultiPolygon as ShapelyMultiPolygon
from shapely import Point as ShapelyPoint
from shapely import Polygon as ShapelyPolygon
from shapely.prepared import prep

from pretty_gpx.common.gpx.gpx_distance import ListLonLat
from pretty_gpx.common.request.osm_name import get_shortest_name
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.utils import are_close
from pretty_gpx.common.utils.utils import EARTH_RADIUS_M
from pretty_gpx.common.utils.utils import MAX_RECURSION_DEPTH
from pretty_gpx.common.utils.utils import points_are_close

DEBUG_DISTANCE = False


@dataclass(kw_only=True)
class SurfacePolygons:
    """Surface Polygons."""
    exterior_polygons: list[Polygon]
    interior_polygons: list[Polygon]


T = TypeVar('T', bound=list[RelationWayGeometryValue] | ListLonLat)
HashTable = dict[tuple[int, int], list[tuple[int, str]]]


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


def simplify_ways(coordinates: list[ListLonLat],
                  tolerance_m: float = 5) -> list[ListLonLat]:
    """Simplify a list of ways using Douglas-Peucker algorithm from shapely."""
    tolerance = np.rad2deg(tolerance_m/EARTH_RADIUS_M)
    total_hausdorff_distance = 0
    logger.debug("Merge ways")
    coordinates = merge_ways(coordinates, eps=tolerance, verbose=DEBUG_DISTANCE)
    simplified_ways = []
    for way in coordinates:
        line = LineString(way)
        simplified_line = line.simplify(tolerance)
        simplified_ways.append(list(simplified_line.coords))
        if DEBUG_DISTANCE:
            total_hausdorff_distance += EARTH_RADIUS_M*np.deg2rad(line.hausdorff_distance(simplified_line))
    if DEBUG_DISTANCE:
        logger.info(f"Hausdorff distance simplified {total_hausdorff_distance:.2e}m")
    return simplified_ways


@profile
def get_ways_coordinates_from_results(api_result: Result) -> list[ListLonLat]:
    """Get the lat/lon nodes coordinates of the ways from the overpass API result."""
    ways_coords = []
    for way in api_result.ways:
        road = get_way_coordinates(way)
        if len(road) > 0:
            ways_coords.append(road)
    ways_coords = simplify_ways(coordinates=ways_coords)
    return ways_coords


@profile
def get_way_coordinates(way: Way) -> ListLonLat:
    """Get the lat/lon nodes coordinates of a ways."""
    return [(float(node.lon), float(node.lat))
            for node in way.get_nodes(resolve_missing=True)
            if node.lon is not None and node.lat is not None]


@profile
def get_rivers_polygons_from_lines(api_result: Result,
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
        line = cast(LineString, line.simplify(0.5 * np.rad2deg(width / EARTH_RADIUS_M)))
        # Transforms the line into a polygon with
        # a buffer around the line with half the width
        buffered = line.buffer(width/2.0)
        if isinstance(buffered, ShapelyPolygon):
            # TODO: Check that multipolygons are not useful and can be skiped
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


@profile
def get_polygons_from_relations(results: Result) -> list[ShapelyPolygon]:
    """Get the shapely polygons from the results with all the relations obtained with the Overpass API."""
    polygon_l = []
    relations = results.get_relations()
    for i in range(len(relations)):
        relation_id = relations[i].id
        relation = results.get_relation(rel_id=relation_id, resolve_missing=True)
        polygon_l += get_polygons_from_relation(relation)
    return polygon_l


@profile
def get_polygons_from_relation(relation: Relation) -> list[ShapelyPolygon]:
    """Get the polygons from a single relation."""
    polygon_l = []
    relation_members = relation.members
    if relation_members is not None:
        outer_geometry_relation_i: list[list[RelationWayGeometryValue]] = []
        inner_geometry_relation_i: list[list[RelationWayGeometryValue]] = []
        outer_geometry_relation_i, inner_geometry_relation_i = get_members_from_relation(relation=relation,
                                                                                         recursion_depth=0)

        # Tolerance is 5m near the point (converted to lon/lat)
        eps = 5./EARTH_RADIUS_M*180/np.pi

        # To avoid the max_reccursion_depth system error on very large relations
        depth_outer = min(max(len(outer_geometry_relation_i)//50, 4), MAX_RECURSION_DEPTH)
        depth_inner = min(max(len(inner_geometry_relation_i)//50, 4), MAX_RECURSION_DEPTH)
        outer_geometry_relation_i = merge_ways_closed_shapes(outer_geometry_relation_i,
                                                             eps=eps,
                                                             max_depth=depth_outer,
                                                             id=relation.id)
        inner_geometry_relation_i = merge_ways_closed_shapes(inner_geometry_relation_i,
                                                             eps=eps,
                                                             max_depth=depth_inner,
                                                             id=relation.id)

        polygon_l += create_polygons_from_geom(outer_geometry_relation_i, inner_geometry_relation_i, id=relation.id)

    return polygon_l


def is_a_closed_shape(geometry: list[RelationWayGeometryValue], eps: float = 1e-5) -> bool:
    """Check if a geometry is closed (e.g. last point = first point)."""
    lon_start, lon_end = float(geometry[0].lon), float(geometry[-1].lon)
    lat_start, lat_end = float(geometry[0].lat), float(geometry[-1].lat)
    return are_close(lon_start, lon_end, eps=eps) and are_close(lat_start, lat_end, eps=eps)


@profile
def merge_ways_closed_shapes(segments: list[list[RelationWayGeometryValue]],
                             eps: float = 1e-5,
                             max_depth: int = 2,
                             id: int = -1) -> list[list[RelationWayGeometryValue]]:
    """Merge ways until all ways create only closed shape or the max_depth is reached.

    This is needed because for closed shapes the algorithm sometimes miss complex/multiple merges
    that occurs at the same point in different direction.
    Or we do not want to complexify the merge way algorithm to have a O(n^2) complexity so to keep
    the O(nlog(n)) complexity in the large majority of cases, we add extra checks only for closed shapes. 
    """
    depth = 0
    all_closed = False if len(segments) > 1 else True
    nb_open_geom = 0
    nb_open_geom_prev = -1

    while depth < max_depth and not all_closed and len(segments) > 1:
        segments = merge_ways(segments, eps=eps, verbose=False)
        for segment in segments:
            if not is_a_closed_shape(segment, eps):
                nb_open_geom += 1

        all_closed = nb_open_geom == 0
        depth += 1
        if len(segments) == 1 and nb_open_geom == 1:
            segments.append(segments[0])
            all_closed = True
            break

        if nb_open_geom == nb_open_geom_prev:
            break
        nb_open_geom_prev = nb_open_geom

    if depth > 1 and all_closed:
        logger.debug(f"Merging closed shapes used {depth} tries to obtain only closed shapes")

    if not all_closed:
        logger.warning(f"Relation {id} Despite {depth} retries, there are still {nb_open_geom} unclosed geometries")

    return segments


@profile
def get_members_from_relation(relation: Relation,
                              recursion_depth: int = 0) -> tuple[list[list[RelationWayGeometryValue]],
                                                                 list[list[RelationWayGeometryValue]]]:
    """Get the members from a relation and classify them by their role."""
    relation_members = relation.members
    outer_geometry_l: list[list[RelationWayGeometryValue]] = []
    inner_geometry_l: list[list[RelationWayGeometryValue]] = []
    if relation_members is None or recursion_depth >= MAX_RECURSION_DEPTH:
        if recursion_depth >= MAX_RECURSION_DEPTH:
            logger.warning("Max Recursion depth exceeded in get_members_from_relation function")
        return outer_geometry_l, inner_geometry_l
    for member in relation_members:
        if type(member) == RelationRelation:
            logger.debug("Found a RelationRelation i.e. a relation in the members of a relation")
            relation_inside_member = member.resolve(resolve_missing=True)
            outer_subrelation, inner_subrelation = get_members_from_relation(relation=relation_inside_member,
                                                                             recursion_depth=recursion_depth+1)
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
        elif type(member) == RelationNode:
            continue
        else:
            raise TypeError(
                f"Unexpected member type {type(member)} not in [RelationWay, RelationRelation, RelationNode]")
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


def create_hash_table(segments: list[Segment], eps: float = 1e-4) -> HashTable:
    """Creates a hash table with the start point and the end point using eps as tolerance."""
    point_to_segments: HashTable = {}
    for i, segment in enumerate(segments):
        start_hash, end_hash = hash_point(segment.start, eps), hash_point(segment.end, eps)
        if start_hash not in point_to_segments:
            point_to_segments[start_hash] = []
        if end_hash not in point_to_segments:
            point_to_segments[end_hash] = []
        point_to_segments[start_hash].append((i, 'start'))
        point_to_segments[end_hash].append((i, 'end'))
    return point_to_segments


def remove_segment_from_hash(hash_table: HashTable, segment_index: int, point_hash: tuple[int, int]) -> None:
    """Remove a segment from the hash table."""
    if point_hash in hash_table:
        hash_table[point_hash] = [entry for entry in hash_table[point_hash] if entry[0] != segment_index]
        if not hash_table[point_hash]:
            del hash_table[point_hash]


def get_neighbor_hashes(point_hash: tuple[int, int]) -> list[tuple[int, int]]:
    """Get neighbor hashes of a point."""
    return [
        point_hash,
        (point_hash[0]-1, point_hash[1]),
        (point_hash[0]+1, point_hash[1]),
        (point_hash[0], point_hash[1]-1),
        (point_hash[0], point_hash[1]+1),
        (point_hash[0]-1, point_hash[1]-1),
        (point_hash[0]-1, point_hash[1]+1),
        (point_hash[0]+1, point_hash[1]-1),
        (point_hash[0]+1, point_hash[1]+1)
    ]


def try_merge_at_point(current_segment: Segment,
                       point_type: str,
                       hash_table: HashTable,
                       segments: list[Segment],
                       merged_geom: list,
                       eps: float) -> tuple[bool, list, Segment]:
    """Try to merge segments at either start or end point. Returns (success, updated_merged_geometry, next_segment)."""
    is_end_point = point_type == 'end'
    current_point = current_segment.end if is_end_point else current_segment.start
    point_hash = hash_point(current_point, eps)
    neighbor_hashes = get_neighbor_hashes(point_hash)

    for neighbor_hash in neighbor_hashes:
        if neighbor_hash not in hash_table:
            continue

        for j, end_type in hash_table[neighbor_hash]:
            next_segment = segments[j]
            if next_segment.merged:
                continue

            compare_point = next_segment.start if end_type == 'start' else next_segment.end
            if not points_are_close(current_point, compare_point, eps=eps):
                continue

            next_segment.merged = True
            next_start_hash = hash_point(next_segment.start, eps)
            next_end_hash = hash_point(next_segment.end, eps)
            remove_segment_from_hash(hash_table, j, next_start_hash)
            remove_segment_from_hash(hash_table, j, next_end_hash)

            # Update geometry and segment depending on the typology of the merge
            if is_end_point:
                if end_type == 'end':
                    next_segment.geom.reverse()
                merged_geom.extend(next_segment.geom[1:])
                current_segment_start = current_segment.start
                current_segment_end = next_segment.end if end_type == 'start' else next_segment.start
            else:
                if end_type == 'start':
                    next_segment.geom.reverse()
                merged_geom = next_segment.geom[:-1] + merged_geom
                current_segment_start = next_segment.end if end_type == 'start' else next_segment.start
                current_segment_end = current_segment.end

            next_segment.start = current_segment_start
            next_segment.end = current_segment_end

            return True, merged_geom, next_segment

    # If no success return a dummy segment
    return False, merged_geom, Segment((0, 0), (0, 0), [])


def merge_segments_from_hash(segments: list[Segment],
                             hash_table: dict[tuple[int, int], list[tuple[int, str]]],
                             eps: float = 1e-4) -> list[T]:
    """Merge the segments localized using the hash table and update the hash table after each merge."""
    merged_segments = []

    for i, segment in enumerate(segments):
        if segment.merged:
            continue

        current_segment: Segment = segment
        current_segment.merged = True
        merged_geom = current_segment.geom[:]

        # Remove segment from hash table
        start_hash = hash_point(current_segment.start, eps)
        end_hash = hash_point(current_segment.end, eps)
        remove_segment_from_hash(hash_table, i, start_hash)
        remove_segment_from_hash(hash_table, i, end_hash)

        # Continue merging until no more connected segments are found
        keep_merging = True
        while keep_merging:
            keep_merging = False

            # Try merging at both end and start points
            for point_type in ['end', 'start']:
                success, merged_geom, next_segment = try_merge_at_point(current_segment=current_segment,
                                                                        point_type=point_type,
                                                                        hash_table=hash_table,
                                                                        segments=segments,
                                                                        merged_geom=merged_geom,
                                                                        eps=eps)

                if success:
                    current_segment = next_segment
                    keep_merging = True
                    break  # Restart the start/end loop to recheck both edges

        new_start_hash = hash_point(current_segment.start, eps)
        new_end_hash = hash_point(current_segment.end, eps)
        hash_table.setdefault(new_start_hash, []).append((i, 'start'))
        hash_table.setdefault(new_end_hash, []).append((i, 'end'))

        merged_segments.append(merged_geom)

    return merged_segments


def merge_ways(geometry_l: list[T],
               eps: float = 1e-5,
               verbose: bool = False) -> list[T]:
    """Merge the connected ways obtained by overpass together."""
    segments_l = [Segment(*get_first_and_last_coords(geom), geom) for geom in geometry_l]
    hash_table = create_hash_table(segments=segments_l,
                                   eps=eps)
    merged_segments: list[T] = merge_segments_from_hash(segments=segments_l,
                                                        hash_table=hash_table,
                                                        eps=eps)
    n_merged = len(geometry_l) - len(merged_segments)
    if verbose and n_merged > 0:
        logger.info(f"{n_merged} segments merged")
    return merged_segments


@profile
def create_polygons_from_geom(outer_geoms: list[list[RelationWayGeometryValue]],
                              inner_geoms: list[list[RelationWayGeometryValue]],
                              id: int = 0) -> list[ShapelyPolygon]:
    """Create shapely polygons (defined by the exterior shell and the holes) for a single relation."""
    # If multiple outer shells are there, creates multiple polygons instead of a shapely.MultiPolygons
    # Therefore for all relations, the area are described using only ShapelyPolygons
    polygon_l = []
    not_closed = 0
    skipped_inners = 0

    # Pre-process inner geometries
    inner_rings = []
    for geom in inner_geoms:
        points = get_lat_lon_from_geometry(geom)
        if len(points) >= 4:
            inner_rings.append((ShapelyLinearRing(points),
                                ShapelyPoint(points[0]),
                                ShapelyPoint(points[len(points)//2])))
        else:
            skipped_inners += 1

    inner_points = []
    for outer_geom in outer_geoms:
        point_l = get_lat_lon_from_geometry(outer_geom)
        if len(point_l) < 4:
            continue
        if point_l[0] != point_l[-1]:
            not_closed += 1

        outer_polygon = ShapelyPolygon(point_l)
        prepared_polygon_i = prep(outer_polygon)

        holes_i = []
        other_holes = []
        for hole, first_point, middle_point in inner_rings:
            if prepared_polygon_i.contains(first_point) or prepared_polygon_i.contains(middle_point):
                # Relaxation of the constraint in order to validate some geometries that are on the border
                holes_i.append(hole)
            else:
                other_holes.append((hole, first_point))
        polygon_l.append(ShapelyPolygon(shell=outer_polygon.exterior,
                                        holes=holes_i))
        inner_points = other_holes
    if len(inner_points) > 0:
        logger.warning(f"Relation {id}. Could not find an outer for all inner geometries, {len(inner_geoms)} "
                       f"inner geometr{'y is' if len(inner_geoms) == 1 else 'ies are'} unused")
    if skipped_inners:
        logger.warning(f"Skipped {skipped_inners} inner geometr{'y' if skipped_inners == 1 else 'ies'} "
                       f"due to having fewer than 4 points")
    return polygon_l


def get_lat_lon_from_geometry(geom: list[RelationWayGeometryValue],
                              tolerance_m: float = 5) -> ListLonLat:
    """Returns latitude and longitude points in order to create a shapely shape."""
    point_l = []
    tolerance = np.rad2deg(tolerance_m/EARTH_RADIUS_M)
    for point in geom:
        point_l.append((float(point.lon), float(point.lat)))
    line = LineString(point_l)
    simplified_line = line.simplify(tolerance)
    return list(simplified_line.coords)


@profile
def create_patch_collection_from_polygons(polygons_l: list[ShapelyPolygon]) -> SurfacePolygons:
    """Create a patch list."""
    patches_exterior: list[Polygon] = []
    patches_interior: list[Polygon] = []
    for geometry in polygons_l:

        exterior_coords = np.asarray(geometry.exterior.coords)
        patches_exterior.append(Polygon(exterior_coords))

        interiors = [np.asarray(interior.coords) for interior in list(geometry.interiors)]
        patches_interior.extend(Polygon(interior) for interior in interiors)

    surface = SurfacePolygons(exterior_polygons=patches_exterior,
                              interior_polygons=patches_interior)

    return surface


def process_around_ways_and_relations(api_result: Result) -> dict[str, tuple[float, float]]:
    """Create a dict of POI with name and coordinates."""
    ways = api_result.ways
    relations = api_result.relations
    output: dict[str, tuple[float, float]] = dict()
    for way in ways:
        name = get_shortest_name(way)
        if name is not None:
            output[name] = (way.center_lon, way.center_lat)
    for relation in relations:
        name = get_shortest_name(relation)
        if name is not None:
            output[name] = (relation.center_lon, relation.center_lat)
    return output
