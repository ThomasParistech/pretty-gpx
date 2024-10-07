#!/usr/bin/python3
"""Overpass Processing."""

from dataclasses import dataclass

import numpy as np
import overpy
from matplotlib.patches import Polygon
from shapely import LineString
from shapely import MultiPolygon as ShapelyMultiPolygon
from shapely import Point as ShapelyPoint
from shapely import Polygon as ShapelyPolygon

from pretty_gpx.common.data.overpass_request import ListLonLat
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.utils import are_close


@dataclass(kw_only=True)
class SurfacePolygons:
    """Surface Polygons."""
    exterior_polygons: list[Polygon]
    interior_polygons: list[Polygon]


def get_ways_coordinates_from_results(api_result: overpy.Result) -> list[ListLonLat]:
    """Get the lat/lon nodes coordinates of the ways from the overpass API result."""
    ways_coords = []
    for way in api_result.ways:
        road = [(float(node.lon), float(node.lat))
                for node in way.get_nodes(resolve_missing=True)]
        if len(road) > 0:
            ways_coords.append(road)
    return ways_coords



@profile
def get_rivers_polygons_from_lines( api_result: overpy.Result,
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
def get_polygons_from_closed_ways(ways_l: list[overpy.Way]) -> list[ShapelyPolygon]:
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
def get_polygons_from_relations(results: overpy.Result) -> list[ShapelyPolygon]:
    """Get the shapely polygons from the results with all the relations obtained with the Overpass API."""
    polygon_l = []
    relations = results.get_relations()
    for i in range(len(relations)):
        relation_id = relations[i].id
        relation = results.get_relation(rel_id=relation_id, resolve_missing=True)
        polygon_l += get_polygons_from_relation(relation)
    return polygon_l


def get_polygons_from_relation(relation: overpy.Relation) -> list[ShapelyPolygon]:
    """Get the polygons from a single relation."""
    polygon_l = []
    relation_members = relation.members
    if relation_members is not None:
        outer_geometry_relation_i: list[list[overpy.RelationWayGeometryValue]] = []
        inner_geometry_relation_i: list[list[overpy.RelationWayGeometryValue]] = []
        outer_geometry_relation_i, inner_geometry_relation_i = get_members_from_relation(relation)

        # TODO: calculate eps to be 0.5m in lat/lon near the points
        outer_geometry_relation_i = merge_ways(outer_geometry_relation_i, eps=1e-3)
        inner_geometry_relation_i = merge_ways(inner_geometry_relation_i, eps=1e-3)

        polygon_l += create_polygons_from_geom(outer_geometry_relation_i, inner_geometry_relation_i)

    return polygon_l


def get_members_from_relation(relation: overpy.Relation) -> tuple[list[list[overpy.RelationWayGeometryValue]],
                                                                  list[list[overpy.RelationWayGeometryValue]]]:
    """Get the members from a relation and classify them by their role."""
    relation_members = relation.members
    if relation_members is not None:
        outer_geometry_l = []
        inner_geometry_l = []
        for member in relation_members:
            if type(member) == overpy.RelationRelation:
                logger.debug("Found a RelationRelation i.e. a relation in the members of a relation")
                relation_inside_member = member.resolve(resolve_missing=True)
                outer_subrelation, inner_subrelation = get_members_from_relation(relation_inside_member)
                outer_geometry_l += outer_subrelation
                inner_geometry_l += inner_subrelation
            elif type(member) == overpy.RelationWay:
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
                    f"Unexpected member type {type(member)} not in [overpy.RelationWay, overpy.RelationRelation]")
    return outer_geometry_l, inner_geometry_l


def merge_ways(geometry_l: list[list[overpy.RelationWayGeometryValue]],
               eps: float = 1e-3) -> list[list[overpy.RelationWayGeometryValue]]:
    """Try to merge all members that have a common starting/ending point."""
    # Indeed, the relations member are sometimes splitted, e.g. the outer line can be made of multiple ways
    p = 0
    nb_merged = 0
    while p < len(geometry_l):
        q = p+1
        while q < len(geometry_l):
            geom_p = geometry_l[p]
            x_p_first, y_p_first = float(geom_p[0].lat), float(geom_p[0].lon)
            x_p_last, y_p_last = float(geom_p[-1].lat), float(geom_p[-1].lon)
            geom_q = geometry_l[q]
            x_q_first, y_q_first = float(geom_q[0].lat), float(geom_q[0].lon)
            x_q_last, y_q_last = float(geom_q[-1].lat), float(geom_q[-1].lon)

            if are_close(x_p_first, x_q_first, eps=eps) and are_close(y_p_first, y_q_first, eps=eps):
                geometry_l[q].reverse()
                geometry_l[p] = geometry_l[q] + geometry_l[p]
                del geometry_l[q]
                q = p+1
                nb_merged += 1
            elif are_close(x_p_last, x_q_last, eps=eps) and are_close(y_p_last, y_q_last, eps=eps):
                geometry_l[q].reverse()
                geometry_l[p] = geometry_l[p] + geometry_l[q]
                del geometry_l[q]
                q = p+1
                nb_merged += 1
            elif are_close(x_p_first, x_q_last, eps=eps) and are_close(y_p_first, y_q_last, eps=eps):
                geometry_l[p] = geometry_l[q] + geometry_l[p]
                del geometry_l[q]
                q = p+1
                nb_merged += 1
            elif are_close(x_p_last, x_q_first, eps=eps) and are_close(y_p_last, y_q_first, eps=eps):
                geometry_l[p] = geometry_l[p] + geometry_l[q]
                del geometry_l[q]
                q = p+1
                nb_merged += 1
            else:
                q += 1
        p += 1
    logger.debug(f"{nb_merged:.0f} segments merged")
    return geometry_l


def create_polygons_from_geom(outer_geoms: list[list[overpy.RelationWayGeometryValue]],
                              inner_geoms: list[list[overpy.RelationWayGeometryValue]]) -> list[ShapelyPolygon]:
    """Create shapely polygons (defined by the exterior shell and the holes) for a single relation."""
    # If multiple outer shells are there, creates multiple polygons instead of a shapely.MultiPolygons
    # Therefore for all relations, the area are described using only ShapelyPolygons
    polygon_l = []
    for outer_geom in outer_geoms:
        point_l = get_lat_lon_from_geometry(outer_geom)
        if len(point_l) <= 4:
            continue
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
    return polygon_l


def get_lat_lon_from_geometry(geom: list[overpy.RelationWayGeometryValue]) -> ListLonLat:
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
