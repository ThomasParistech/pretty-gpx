#!/usr/bin/python3
"""City Roads."""
import os
import shapely
import overpy
import numpy as np
from enum import auto
from enum import Enum

from tqdm import tqdm

from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.gpx.overpass import overpass_query
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.utils import is_close_to
from pretty_gpx.common.utils.utils import EARTH_RADIUS
from pretty_gpx.common.utils.logger import logger

ROADS_CACHE = GpxDataCacheHandler(name='roads', extension='.pkl')
RIVERS_CACHE = GpxDataCacheHandler(name='rivers', extension='.pkl')
FORESTS_CACHE = GpxDataCacheHandler(name='forests', extension='.pkl')


class CityRoadType(Enum):
    """City Road Type."""
    HIGHWAY = auto()
    SECONDARY_ROAD = auto()
    STREET = auto()
    ACCESS_ROAD = auto()

class AirportRoadsType(Enum):
    RUNWAY = auto()
    TAXIWAY = auto()

HIGHWAY_TAGS_PER_CITY_ROAD_TYPE = {
    CityRoadType.HIGHWAY: ["motorway", "trunk", "primary"],
    CityRoadType.SECONDARY_ROAD: ["tertiary", "secondary"],
    CityRoadType.STREET: ["residential", "living_street"],
    CityRoadType.ACCESS_ROAD: ["unclassified", "service"]
}

AIRWAY_TAGS_PER_AIRPORT_ROAD_TYPE = {
    AirportRoadsType.RUNWAY: ["runway"],
    AirportRoadsType.TAXIWAY: ["taxiway"]
}


RoadLonLat = list[tuple[float, float]]
CityRoads = dict[CityRoadType, list[RoadLonLat]]


def download_city_roads(bounds: GpxBounds) -> CityRoads:
    """Download roads map from OpenStreetMap.

    Args:
        bounds: GPX bounds

    Returns:
        List of roads (sequence of lon, lat coordinates) for each road type
    """
    cache_pkl = ROADS_CACHE.get_path(bounds)

    if os.path.isfile(cache_pkl):
        roads: CityRoads = read_pickle(cache_pkl)
    else:
        roads = {city_road_type: _query_roads(bounds, city_road_type)
                 for city_road_type in tqdm(CityRoadType)}
        write_pickle(cache_pkl, roads)

    return roads


def download_city_forests(bounds: GpxBounds) -> list[shapely.Polygon]:
    """Download forest area from OpenStreetMap.

    Args:
        bounds: GPX bounds

    Returns:
        List of shapely.Polygon of all forests/parks
    """
    cache_pkl = FORESTS_CACHE.get_path(bounds)

    if os.path.isfile(cache_pkl):
        forests: list[shapely.Polygon] = read_pickle(cache_pkl)
    else:
        forests_osm_results = _query_forests(bounds=bounds)
        forests = get_polygons_from_relations(results=forests_osm_results)
        write_pickle(cache_pkl, forests)
    return forests


def download_city_rivers(bounds: GpxBounds) -> list[shapely.Polygon]:
    """Download rivers area from OpenStreetMap.

    Args:
        bounds: GPX bounds

    Returns:
        List of shapely.Polygon of all forests/parks
    """
    cache_pkl = RIVERS_CACHE.get_path(bounds)

    if os.path.isfile(cache_pkl):
        rivers: list[shapely.Polygon] = read_pickle(cache_pkl)
    else:
        rivers_relation_results = _query_rivers_relations(bounds=bounds)
        rivers_way_results = _query_rivers_ways(bounds=bounds)
        rivers = get_polygons_from_relations(results=rivers_relation_results)
        rivers += get_polygons_from_closed_ways(rivers_way_results.ways)
        write_pickle(cache_pkl, rivers)
    return rivers


def _query_roads(bounds: GpxBounds, city_road_type:  CityRoadType) -> list[RoadLonLat]:
    """Query the overpass API to get the roads of a city."""
    highway_tags_str = "|".join(HIGHWAY_TAGS_PER_CITY_ROAD_TYPE[city_road_type])
    result = overpass_query([f"way['highway'~'({highway_tags_str})']"], bounds, include_way_nodes=True)

    roads: list[RoadLonLat] = []
    roads = get_ways_coordinates_from_results(result)
    return roads


def _query_railways(bounds: GpxBounds) -> list[RoadLonLat]:
    """Query the overpass API to get the railways of a city."""
    result = overpass_query([f"way['railway'~'rail'][!'tunnel']['usage'='main']"], bounds, include_way_nodes=True)
    railways = get_ways_coordinates_from_results(result)
    return railways


def _query_airports_ways(bounds: GpxBounds, airport_way_type:  AirportRoadsType) -> list[RoadLonLat]:
    """Query the overpass API to get the airport runways/taxiways of a city."""
    aeroway_tags_str = "|".join(AIRWAY_TAGS_PER_AIRPORT_ROAD_TYPE[airport_way_type])
    result = overpass_query([f"way['aeroway'~'({aeroway_tags_str})']"], bounds, include_way_nodes=True)
    airport_ways = get_ways_coordinates_from_results(result)
    return airport_ways



def _query_airports_locations(bounds: GpxBounds) -> list[RoadLonLat]:
    """Query the overpass API to get the location of airports."""
    result = overpass_query(["relation['aeroway'='aerodrome']['icao'~'.*']",
                             "way['aeroway'='aerodrome']['icao'~'.*']"], bounds)

    airport_coords = []
    for way in result.ways:
        airport_coords.append((float(way.center_lat),float(way.center_lon)))

    for relation in result.relations:
        airport_coords.append((float(relation.center_lat),float(relation.center_lon)))
    return airport_coords


def _query_forests(bounds: GpxBounds):
    """Query the overpass API to get the parks and forest of a city."""
    result = overpass_query(['relation["leisure"="park"]["type"!="site"]',
                             'relation["leisure"="park"]["type"!="site"]'],
                            bounds,
                            include_way_nodes=True,
                            return_geometry=True)    
    return result


def _query_rivers_relations(bounds: GpxBounds):
    """Query the overpass API to get the rivers of a city using relations."""
    result = overpass_query(['relation["natural"="water"]["water" = "river"]'],
                            bounds,
                            include_way_nodes=True,
                            return_geometry=True)    
    return result


def _query_rivers_ways(bounds: GpxBounds):
    """Query the overpass API to get the rivers of a city using ways."""
    result = overpass_query(['way["natural"="water"]["water" = "river"]'],
                            bounds,
                            include_way_nodes=True,
                            return_geometry=True)    
    return result



def get_polygons_from_closed_ways(ways_l: list[overpy.Way]) -> list[shapely.Polygon]:
    """
    Sometimes ways instead of relations are used to describe an area
    It have an impact on the map mainly for rivers
    """
    river_way_polygon = []
    for way in ways_l:
        way_coords = []
        for node in way.get_nodes(resolve_missing=True):
            way_coords.append((float(node.lat), float(node.lon)))
        if len(way_coords)>0:
            if way_coords[0][0] == way_coords[-1][0] and way_coords[0][1] == way_coords[-1][1]:
                river_way_polygon.append(shapely.Polygon(way_coords))
            else:
                print("WARNING : shape not closed, skipped")
    return river_way_polygon



def get_polygons_from_relations(results: overpy.Result) -> list[shapely.Polygon]:
    """
    Get the shapely polygons from the results with all the relations obtained 
    with the Overpass API
    """
    polygon_l = []
    relations = results.get_relations()
    for i in range(len(relations)):
        relation_id = relations[i].id
        relation = results.get_relation(rel_id=relation_id, resolve_missing=True)
        polygon_l += get_polygons_from_relation(relation)
    return polygon_l


def get_polygons_from_relation(relation: overpy.Relation) -> list[shapely.Polygon]:
    """
    Get the polygons from a single relation
    """
    polygon_l = []
    relation_members = relation.members
    if relation_members is not None:
        outer_geometry_relation_i = []
        inner_geometry_relation_i = []
        outer_geometry_relation_i,inner_geometry_relation_i = get_members_from_relation(relation)

        # TODO calculate eps to be 0.5m in lat/lon near the points
        outer_geometry_relation_i = merge_ways(outer_geometry_relation_i, eps=1e-3)
        inner_geometry_relation_i = merge_ways(inner_geometry_relation_i, eps=1e-3)

        polygon_l += create_polygons_from_geom(outer_geometry_relation_i,inner_geometry_relation_i)
    
    return polygon_l

def get_members_from_relation(relation: overpy.Relation) -> list[overpy.RelationWayGeometryValue,
                                                                 overpy.RelationWayGeometryValue]:
    """
    Get the members from a relation and classify them by their role
    """
    relation_members = relation.members
    if relation_members is not None:
        outer_geometry_l = []
        inner_geometry_l = []
        for member in relation_members:
            if type(member) == overpy.RelationRelation:
                logger.info(f"Found a RelationRelation i.e. a relation in the members of a relation")
                relation_inside_member = member.resolve(resolve_missing=True)
                outer_subrelation,inner_subrelation = get_members_from_relation(relation_inside_member)
                outer_geometry_l += outer_subrelation
                inner_geometry_l += inner_subrelation
            elif type(member) == overpy.RelationWay:
                if member.geometry == None:
                    continue
                if member.role == "outer":
                    outer_geometry_l.append(member.geometry)
                elif member.role == "inner":
                    inner_geometry_l.append(member.geometry)
                else:
                    raise ValueError(f"Unexpected member role in a relation {member.role} not in ['inner','outer']")
            else:
                raise TypeError(f"Unexpected member type {type(member)} not in [overpy.RelationWay, overpy.RelationRelation]")
    return outer_geometry_l,inner_geometry_l


def merge_ways(geometry_l: list[list[overpy.RelationWayGeometryValue]],
               eps: float = 1e-3) -> list[list[overpy.RelationWayGeometryValue]]:
    """
    The relations member are sometimes splitted. For example,
    the outer line can be made of multiple ways. 
    Here we try to merge all members that have a common starting/ending point
    """
    p=0
    nb_merged = 0
    while p < len(geometry_l):
        q = p+1
        while q < len(geometry_l):
            geom_p = geometry_l[p]
            x_p_first,y_p_first = float(geom_p[0].lat),float(geom_p[0].lon)
            x_p_last,y_p_last = float(geom_p[-1].lat),float(geom_p[-1].lon)
            geom_q = geometry_l[q]
            x_q_first,y_q_first = float(geom_q[0].lat),float(geom_q[0].lon)
            x_q_last,y_q_last = float(geom_q[-1].lat),float(geom_q[-1].lon)

            if is_close_to(x_p_first, x_q_first, eps) and is_close_to(y_p_first, y_q_first, eps):
                geometry_l[q].reverse()
                geometry_l[p] =  geometry_l[q] + geometry_l[p]
                del geometry_l[q]
                q = p+1
                nb_merged += 1
            elif is_close_to(x_p_last, x_q_last, eps) and is_close_to(y_p_last, y_q_last, eps):
                geometry_l[q].reverse()
                geometry_l[p] = geometry_l[p] + geometry_l[q]
                del geometry_l[q]
                q = p+1
                nb_merged += 1
            elif is_close_to(x_p_first, x_q_last, eps) and is_close_to(y_p_first, y_q_last, eps):
                geometry_l[p] = geometry_l[q] + geometry_l[p]
                del geometry_l[q]
                q = p+1
                nb_merged += 1
            elif is_close_to(x_p_last, x_q_first, eps) and is_close_to(y_p_last, y_q_first, eps):
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
                              inner_geoms: list[list[overpy.RelationWayGeometryValue]]) -> list[shapely.Polygon]:
    """
    Creates shapely polygons (defined by the exterior shell and the holes) for a single 
    relation. If multiple outer shells are there, creates multiple polygons instead of a 
    shapely.MultiPolygons
    Therefore for all relations, the area are described using only shapely.Polygons
    """
    polygon_l = []
    for outer_geom in outer_geoms:
        point_l = get_lat_lon_from_geometry(outer_geom)
        if len(point_l) <= 4:
            continue
        outer_polygon_i = shapely.Polygon(point_l)
        holes_i = []
        other_holes = []
        for j in range(len(inner_geoms)):
            member_geom = inner_geoms[j]
            inner_shape_point = shapely.Point((float(member_geom[0].lat),float(member_geom[0].lon)))
            if outer_polygon_i.contains(inner_shape_point):
                hole = get_lat_lon_from_geometry(member_geom)
                holes_i.append(hole)
            else:
                other_holes.append(inner_geoms[j])

        polygon_l.append(shapely.Polygon(shell=point_l,
                                         holes=holes_i))
        inner_geoms = other_holes.copy()
    if len(inner_geoms) > 0:
        logger.warning(f"Could not find an outer for all inner geometries, "
                       f"{len(inner_geoms)} inner geometries are unused")
    return polygon_l



def get_lat_lon_from_geometry(geom: list[overpy.RelationWayGeometryValue]) -> list[tuple[float,float]]:
    """Returns latitude and longitude points in order to create a shapely shape"""
    point_l = []
    for point in geom:
        point_l.append((float(point.lat),float(point.lon)))
    return point_l


def get_ways_coordinates_from_results(api_result: overpy.Result) -> list[tuple[list[float],list[float]]]:
    """Get a list of tuples containing the list of x and y coordinates of the road"""
    ways_coords = []
    for way in api_result.ways:
        road = [(float(node.lon), float(node.lat))
                for node in way.get_nodes(resolve_missing=True)]
        if len(road) > 0:
            ways_coords.append(road)
    return ways_coords


def generate_evenly_spaced_sleepers(x: list[float],
                                    y: list[float],
                                    sleeper_distance: float=0.5,
                                    sleeper_length: float=0.05):
    """
    For railways, sleepers are created so that railways are distinguished on the map,
    They are evenly spaced by sleeper_distance in meters and sleeper_length in meters
    """

    # Convert meters to the lat lon degrees
    meters_to_degrees = 180.0/(EARTH_RADIUS*np.pi)

    segments = []
    total_distance = 0
    next_sleeper_distance = sleeper_distance*meters_to_degrees
    sleeper_length = sleeper_length*meters_to_degrees

    for i in range(1, len(x)):
        # Compute distance between consecutive points
        dx = x[i] - x[i - 1]
        dy = y[i] - y[i - 1]
        distance = np.hypot(dx, dy)
        total_distance += distance

        while total_distance >= next_sleeper_distance:
            # interpolate along the segment
            t = (next_sleeper_distance - (total_distance - distance)) / distance
            sleeper_x = x[i - 1] + t * (x[i] - x[i - 1])
            sleeper_y = y[i - 1] + t * (y[i] - y[i - 1])
            
            # Get the perpendicular direction
            dx_grad = np.gradient(x)[i]
            dy_grad = np.gradient(y)[i]
            length = np.hypot(dx_grad, dy_grad)
            perp_dx = -dy_grad / length * sleeper_length
            perp_dy = dx_grad / length * sleeper_length
            
            segments.append([(sleeper_x - perp_dx, sleeper_y - perp_dy), (sleeper_x + perp_dx, sleeper_y + perp_dy)])
            
            # Update the distance for the next sleeper
            next_sleeper_distance += sleeper_distance

    return segments