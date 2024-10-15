#!/usr/bin/python3
"""Airports."""
import os
from enum import auto
from enum import Enum

from tqdm import tqdm

from pretty_gpx.common.data.overpass_processing import get_ways_coordinates_from_results
from pretty_gpx.common.data.overpass_request import ListLonLat
from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling

AIRPORTS_CACHE = GpxDataCacheHandler(name='airports', extension='.pkl')

AIRPORT_ICON_PATH = "assets/icons/airplane.svg"
AIRPORT_ICON_SHARE_OF_X_PLOTTER = 0.02


class AirportRoadsType(Enum):
    """Airport Road Type."""
    RUNWAY = auto()
    TAXIWAY = auto()


AEROWAY_TAGS_PER_AIRPORT_ROAD_TYPE = {
    AirportRoadsType.RUNWAY: ["runway"],
    AirportRoadsType.TAXIWAY: ["taxiway"],
}

QUERY_NAME_PER_AIRPORT_ROAD_TYPE = {
    AirportRoadsType.RUNWAY: "runway",
    AirportRoadsType.TAXIWAY: "taxiway",
}

assert AEROWAY_TAGS_PER_AIRPORT_ROAD_TYPE.keys() == QUERY_NAME_PER_AIRPORT_ROAD_TYPE.keys()

QUERY_NAME_AIRPORTS_CENTERS = "airport_centers"

AirportLocations = list[tuple[float, float]]
AirportRoads = dict[AirportRoadsType, list[ListLonLat]]


@profile
def prepare_download_airports_data(query: OverpassQuery,
                                   bounds: GpxBounds) -> None:
    """Download airports runway, taxiway and location from OpenStreetMap.

    Args:
        query: OverpassQuery class that merge all queries into a single one
        bounds: GPX bounds
    """
    cache_pkl = AIRPORTS_CACHE.get_path(bounds)

    if os.path.isfile(cache_pkl):
        query.add_cached_result(AIRPORTS_CACHE.name, cache_file=cache_pkl)
    else:
        for aeroway_type in tqdm(AirportRoadsType):
            aeroway_type_tags_str = "|".join(AEROWAY_TAGS_PER_AIRPORT_ROAD_TYPE[aeroway_type])
            query.add_overpass_query(QUERY_NAME_PER_AIRPORT_ROAD_TYPE[aeroway_type],
                                     [f"way['aeroway'~'({aeroway_type_tags_str})']"],
                                     bounds,
                                     include_way_nodes=True,
                                     add_relative_margin=None)
        query.add_overpass_query(QUERY_NAME_AIRPORTS_CENTERS,
                                 ["relation['aeroway'='aerodrome']['icao'~'.*']",
                                  "way['aeroway'='aerodrome']['icao'~'.*']"],
                                 bounds,
                                 return_center_only=True,
                                 include_way_nodes=False,
                                 add_relative_margin=None)

@profile
def process_airports_data(query: OverpassQuery,
                          bounds: GpxBounds) -> tuple[dict[AirportRoadsType,list[ListLonLat]],
                                                      ListLonLat]:
    """Read the overpass API results to get the airports and their runways/taxiways."""
    if query.is_cached(AIRPORTS_CACHE.name):
        cache_file = query.get_cache_file(AIRPORTS_CACHE.name)
        airports_ways, airports_centers = read_pickle(cache_file)
    else:
        with Profiling.Scope("Process airports"):
            airports_ways = dict()
            for aeroway_type,query_name in QUERY_NAME_PER_AIRPORT_ROAD_TYPE.items():
                result = query.get_query_result(query_name)
                airports_ways[aeroway_type] = get_ways_coordinates_from_results(result)
            # Get airport centers
            airports_centers = []
            airports_centers_osm = query.get_query_result(QUERY_NAME_AIRPORTS_CENTERS)
            for way in airports_centers_osm.ways:
                center = (float(way.center_lon),float(way.center_lat))
                if bounds.is_in_bounds(*center):
                    airports_centers.append((float(way.center_lon),float(way.center_lat)))
            for relation in airports_centers_osm.relations:
                center = (float(relation.center_lon),float(relation.center_lat))
                if bounds.is_in_bounds(*center):
                    airports_centers.append((float(relation.center_lon),float(relation.center_lat)))
        # Add to cache
        cache_pkl = AIRPORTS_CACHE.get_path(bounds)
        write_pickle(cache_pkl, (airports_ways, airports_centers))
        query.add_cached_result(AIRPORTS_CACHE.name, cache_file=cache_pkl)
    return airports_ways, airports_centers
