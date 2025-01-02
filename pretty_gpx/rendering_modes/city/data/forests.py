#!/usr/bin/python3
"""Rivers."""
import os

from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.request.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.request.overpass_processing import create_patch_collection_from_polygons
from pretty_gpx.common.request.overpass_processing import get_polygons_from_closed_ways
from pretty_gpx.common.request.overpass_processing import get_polygons_from_relations
from pretty_gpx.common.request.overpass_processing import SurfacePolygons
from pretty_gpx.common.request.overpass_request import OverpassQuery
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling

FORESTS_CACHE = GpxDataCacheHandler(name='forests', extension='.pkl')

FORESTS_WAY_NAME = "forests_way"
FORESTS_RELATION_NAME = "forests_relation"
FARMLAND_WAY_NAME = "farmland_way"
FARMLAND_RELATION_NAME = "farmland_relation"


@profile
def prepare_download_city_forests(query: OverpassQuery,
                                  bounds: GpxBounds) -> None:
    """Add the queries for city rivers inside the global OverpassQuery."""
    cache_pkl = FORESTS_CACHE.get_path(bounds)

    if os.path.isfile(cache_pkl):
        query.add_cached_result(FORESTS_CACHE.name, cache_file=cache_pkl)
        return

    query.add_overpass_query(array_name=FORESTS_RELATION_NAME,
                             query_elements=['relation["leisure"="park"]["type"!="site"]',
                                             'relation["landuse"~"(forest|meadow|orchard|vineyard|plant_nursery)"]'
                                             '["type"!="site"]',
                                             'relation["leisure"~"(sports_centre|golf_course)"]["type"!="site"]'],
                             bounds=bounds,
                             include_way_nodes=True,
                             include_relation_members_nodes=True,
                             return_geometry=True)

    query.add_overpass_query(array_name=FORESTS_WAY_NAME,
                             query_elements=['way["natural"="grassland"]',
                                             'way["landuse"~"(forest|meadow|orchard|vineyard|plant_nursery)"]'],
                             bounds=bounds,
                             include_way_nodes=True,
                             return_geometry=True)

    query.add_overpass_query(array_name=FARMLAND_RELATION_NAME,
                             query_elements=['relation["landuse"~"(farmland)"]'],
                             bounds=bounds,
                             include_way_nodes=True,
                             include_relation_members_nodes=True,
                             return_geometry=True)

    query.add_overpass_query(array_name=FARMLAND_WAY_NAME,
                             query_elements=['way["landuse"~"(farmland)"]'],
                             bounds=bounds,
                             include_way_nodes=True,
                             return_geometry=True)


@profile
def process_city_forests(query: OverpassQuery,
                         bounds: GpxBounds) -> tuple[SurfacePolygons, SurfacePolygons]:
    """Process the overpass API result to get the rivers of a city."""
    if query.is_cached(FORESTS_CACHE.name):
        cache_file = query.get_cache_file(FORESTS_CACHE.name)
        return read_pickle(cache_file)

    with Profiling.Scope("Process Forests"):
        forests_relation_results = query.get_query_result(FORESTS_RELATION_NAME)
        forests_way_results = query.get_query_result(FORESTS_WAY_NAME)
        forests_relations = get_polygons_from_relations(results=forests_relation_results)
        forests_ways = get_polygons_from_closed_ways(forests_way_results.ways)
        logger.info(f"Found {len(forests_relations)} polygons for forests "
                    f"with relations and {len(forests_ways)} with forests")
        forests = forests_relations + forests_ways
        forests_patches = create_patch_collection_from_polygons(forests)

        farmland_relation_results = query.get_query_result(FARMLAND_RELATION_NAME)
        farmland_way_results = query.get_query_result(FARMLAND_WAY_NAME)
        farmland_relations = get_polygons_from_relations(results=farmland_relation_results)
        farmland_ways = get_polygons_from_closed_ways(farmland_way_results.ways)
        farmland = farmland_relations + farmland_ways
        farmland_patches = create_patch_collection_from_polygons(farmland)

    cache_pkl = FORESTS_CACHE.get_path(bounds)
    write_pickle(cache_pkl, (forests_patches, farmland_patches))
    query.add_cached_result(FORESTS_CACHE.name, cache_file=cache_pkl)

    return forests_patches, farmland_patches
