#!/usr/bin/python3
"""Forests"""
import os
import numpy as np


from matplotlib.patches import Polygon
from shapely import Polygon as ShapelyPolygon

from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.data.overpass_request import overpass_query
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.data.overpass_processing import Surface_Polygons
from pretty_gpx.common.data.overpass_processing import create_patch_collection_from_polygons
from pretty_gpx.common.data.overpass_processing import get_polygons_from_relations




FORESTS_CACHE = GpxDataCacheHandler(name='forests', extension='.pkl')


def download_city_forests(bounds: GpxBounds) -> Surface_Polygons:
    """Download forest area from OpenStreetMap.

    Args:
        bounds: GPX bounds

    Returns:
        List of ShapelyPolygon of all forests/parks
    """
    cache_pkl = FORESTS_CACHE.get_path(bounds)

    if os.path.isfile(cache_pkl):
        forests_patches: Surface_Polygons = read_pickle(cache_pkl)
    else:
        forests_osm_results = _query_forests(bounds=bounds)
        forests = get_polygons_from_relations(results=forests_osm_results)
        forests_patches = create_patch_collection_from_polygons(forests)
        write_pickle(cache_pkl, forests_patches)
    return forests_patches




def _query_forests(bounds: GpxBounds):
    """Query the overpass API to get the parks and forest of a city."""
    result = overpass_query(['relation["leisure"="park"]["type"!="site"]',
                             'relation["landuse"="forest"]["type"!="site"]'],
                            bounds,
                            include_way_nodes=True,
                            return_geometry=True)    
    return result

