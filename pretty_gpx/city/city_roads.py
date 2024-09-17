#!/usr/bin/python3
"""City Roads."""
import os
from enum import auto
from enum import Enum

from tqdm import tqdm

from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.gpx.overpass import overpass_query
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle

ROADS_CACHE = GpxDataCacheHandler(name='roads', extension='.pkl')


class CityRoadType(Enum):
    """City Road Type."""
    HIGHWAY = auto()
    SECONDARY_ROAD = auto()
    STREET = auto()
    ACCESS_ROAD = auto()


HIGHWAY_TAGS_PER_CITY_ROAD_TYPE = {
    CityRoadType.HIGHWAY: ["motorway", "trunk", "primary"],
    CityRoadType.SECONDARY_ROAD: ["tertiary", "secondary"],
    CityRoadType.STREET: ["residential", "living_street"],
    CityRoadType.ACCESS_ROAD: ["unclassified", "service"]
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


def _query_roads(bounds: GpxBounds, city_road_type:  CityRoadType) -> list[RoadLonLat]:
    """Query the overpass API to get the roads of a city."""
    highway_tags_str = "|".join(HIGHWAY_TAGS_PER_CITY_ROAD_TYPE[city_road_type])
    result = overpass_query([f"way['highway'~'({highway_tags_str})']"], bounds, include_way_nodes=True)

    roads: list[RoadLonLat] = []
    for way in result.ways:
        road = [(float(node.lon), float(node.lat))
                for node in way.get_nodes(resolve_missing=True)]
        if len(road) > 0:
            roads.append(road)
    return roads
