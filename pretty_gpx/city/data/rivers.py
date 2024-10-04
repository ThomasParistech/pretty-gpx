#!/usr/bin/python3
"""Rivers."""
import os

from pretty_gpx.common.data.overpass_processing import create_patch_collection_from_polygons
from pretty_gpx.common.data.overpass_processing import get_polygons_from_closed_ways
from pretty_gpx.common.data.overpass_processing import get_polygons_from_relations
from pretty_gpx.common.data.overpass_processing import SurfacePolygons
from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling

RIVERS_CACHE = GpxDataCacheHandler(name='rivers', extension='.pkl')

RIVERS_WAYS_ARRAY_NAME = "rivers_ways"
RIVERS_RELATIONS_ARRAY_NAME = "rivers_relations"


RIVERS_WAYS_ARRAY_NAME = "rivers_ways"
RIVERS_RELATIONS_ARRAY_NAME = "rivers_relations"


@profile
def prepare_download_city_rivers(query: OverpassQuery,
                                 bounds: GpxBounds) -> None:
    """Add the queries for city rivers inside the global OverpassQuery."""
    cache_pkl = RIVERS_CACHE.get_path(bounds)

    if os.path.isfile(cache_pkl):
        query.add_cached_result(RIVERS_CACHE.name, cache_file=cache_pkl)
    else:
        query.add_overpass_query(array_name=RIVERS_RELATIONS_ARRAY_NAME,
                                 query_elements=['relation["natural"="water"]["water" = "river"]'],
                                 bounds=bounds,
                                 include_way_nodes=True,
                                 return_geometry=True) 
        query.add_overpass_query(array_name=RIVERS_WAYS_ARRAY_NAME,
                                 query_elements=['way["natural"="water"]["water" = "river"]'],
                                 bounds=bounds,
                                 include_way_nodes=True,
                                 return_geometry=True) 



@profile
def process_city_rivers(query: OverpassQuery,
                        bounds: GpxBounds) -> SurfacePolygons:
    """Process the overpass API result to get the rivers of a city."""
    if query.is_cached(RIVERS_CACHE.name):
        cache_file = query.get_cache_file(RIVERS_CACHE.name)
        rivers_patches = read_pickle(cache_file)
    else:
        with Profiling.Scope("Process Rivers"):
            rivers_relation_results = query.get_query_result(RIVERS_RELATIONS_ARRAY_NAME)
            rivers_way_results = query.get_query_result(RIVERS_WAYS_ARRAY_NAME)
            rivers_relations = get_polygons_from_relations(results=rivers_relation_results)
            rivers_ways = get_polygons_from_closed_ways(rivers_way_results.ways)
            logger.info(f"Found {len(rivers_relations)} polygons for rivers "
                        f"with relations and {len(rivers_ways)} with ways")
            rivers = rivers_relations + rivers_ways
            rivers_patches = create_patch_collection_from_polygons(rivers)
        cache_pkl = RIVERS_CACHE.get_path(bounds)
        write_pickle(cache_pkl, rivers_patches)
        query.add_cached_result(RIVERS_CACHE.name, cache_file=cache_pkl)
    return rivers_patches