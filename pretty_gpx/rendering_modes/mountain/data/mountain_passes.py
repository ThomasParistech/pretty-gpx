#!/usr/bin/python3
"""Mountain Passes."""
import os
from dataclasses import dataclass

from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling


@dataclass
class MountainPass:
    """Mountain pass Data."""
    name: str
    ele: float  # Elevation (in m)
    lon: float
    lat: float


MOUNTAIN_PASSES_ARRAY_NAME = "mountain_passes"


MOUNTAIN_PASS_CACHE = GpxDataCacheHandler(name='mountain_pass', extension='.pkl')


@profile
def prepare_download_mountain_passes(query: OverpassQuery, bounds: GpxBounds) -> None:
    """Add the queries for mountain passes inside the global OverpassQuery."""
    cache_pkl = MOUNTAIN_PASS_CACHE.get_path(bounds)

    if os.path.isfile(cache_pkl):
        query.add_cached_result(MOUNTAIN_PASS_CACHE.name, cache_file=cache_pkl)
        return

    # See https://www.openstreetmap.org/node/4977980007 (Col du Galibier)
    # See https://www.openstreetmap.org/node/12068789882 (Col de la Vanoise)
    # See https://www.openstreetmap.org/node/34975894 (Pic du Cabaliros)
    query.add_overpass_query(array_name=MOUNTAIN_PASSES_ARRAY_NAME,
                             query_elements=["node['natural'='saddle']",
                                             "node['natural'='peak']",
                                             "node['natural'='volcano']",
                                             "node['mountain_pass'='yes']",
                                             "node['hiking'='yes']['tourism'='information']",
                                             "node['hiking'='yes']['information'='guidepost']"],
                             tags=True,
                             return_center_only=True,
                             bounds=bounds,
                             add_relative_margin=0.05)


@profile
def process_mountain_passes(query: OverpassQuery, bounds: GpxBounds) -> list[MountainPass]:
    """Process the overpass API result to get the mountain passes."""
    if query.is_cached(MOUNTAIN_PASS_CACHE.name):
        cache_file = query.get_cache_file(MOUNTAIN_PASS_CACHE.name)
        return read_pickle(cache_file)

    with Profiling.Scope("Process Mountain Passes"):
        results = query.get_query_result(MOUNTAIN_PASSES_ARRAY_NAME)

        passes: list[MountainPass] = []
        for node in results.nodes:
            if "name" in node.tags and "ele" in node.tags:
                ele = str(node.tags["ele"])
                if ele.isnumeric():
                    name = str(node.tags["name"])
                    if "hiking" in node.tags and node.tags["hiking"] == "yes":
                        if not name.lower().startswith(("col ", "golet ", "pic ", "mont ")):
                            continue

                    passes.append(MountainPass(name=name,
                                               ele=float(ele),
                                               lon=float(node.lon),
                                               lat=float(node.lat)))
        logger.info(f"Found {len(passes)} candidate mountain passes")

    cache_pkl = MOUNTAIN_PASS_CACHE.get_path(bounds)
    write_pickle(cache_pkl, passes)
    query.add_cached_result(MOUNTAIN_PASS_CACHE.name, cache_file=cache_pkl)

    return passes
