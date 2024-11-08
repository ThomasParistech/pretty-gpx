#!/usr/bin/python3
"""Overpass API."""

import urllib.parse
import urllib.request
from dataclasses import dataclass
from dataclasses import field

import ujson
from overpy import Area
from overpy import Node
from overpy import Overpass
from overpy import Relation
from overpy import Result
from overpy import Way

from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.common.utils.utils import convert_bytes

DEBUG_OVERPASS_QUERY = False


ListLonLat = list[tuple[float, float]]


@dataclass
class OverpassQuery:
    """Class to store all queries needed, to launch them and to split the result."""
    query_dict: dict[str, str] = field(default_factory=dict)
    query_unprocessed_results: dict[str, Result] = field(default_factory=dict)
    query_cached_results: dict[str, str] = field(default_factory=dict)

    def add_overpass_query(self,
                           array_name: str,
                           query_elements: list[str],
                           bounds: GpxBounds | GpxTrack,
                           include_way_nodes: bool = False,
                           include_relation_members_nodes: bool = False,
                           return_geometry: bool = False,
                           return_center_only: bool = False,
                           add_relative_margin: float | None = None) -> None:
        """Add a query to the list so that all queries can be launch simultaneously."""
        if isinstance(bounds, GpxTrack):
            bounds = bounds.get_bounds()

        if add_relative_margin is not None:
            bounds = bounds.add_relative_margin(add_relative_margin)

        bounds_str = f"({bounds.lat_min:.5f}, {bounds.lon_min:.5f}, {bounds.lat_max:.5f}, {bounds.lon_max:.5f})"

        query_body = "\n".join([f"{element}{bounds_str};" for element in query_elements])

        if return_center_only:
            out_param = "center"
        elif return_geometry:
            out_param = "geom"
        else:
            out_param = ""

        if include_relation_members_nodes:
            # If include_relation_members_nodes and include_way_nodes as
            # the double reccursion is stronger than the simple, there is
            # no problem
            recursion_param = f"(.{array_name};>>;)->.{array_name};\n"
        elif include_way_nodes:
            recursion_param = f"(.{array_name};>;)->.{array_name};\n"
        else:
            recursion_param = ""

        query = f"""(
{query_body}
)->.{array_name};
{recursion_param}
.{array_name} out skel {out_param};"""

        self.query_dict[array_name] = query
        logger.info(f"A query {array_name} has been added to the total query")

    def add_cached_result(self,
                          array_name: str,
                          cache_file: str) -> None:
        """Add the cache file in a dict to be able to use it when processing results."""
        self.query_cached_results[array_name] = cache_file

    @profile
    def merge_queries(self,
                      timeout_s: int = 300,
                      maxsize_b: float = 1e9) -> tuple[str, list[str]]:
        """Merge all queries in a single one."""
        full_query: str = ""
        array_ordered_list: list[str] = []
        for array_name, query in self.query_dict.items():
            array_ordered_list.append(array_name)
            full_query = f"{full_query}\n{query}\n.{array_name} out count;\n\n"
        if full_query != "":
            full_query = f"[timeout:{timeout_s:.0f}][maxsize:{maxsize_b:.0f}][out:json];\n" + full_query
        elif len(self.query_cached_results) == 0:
            logger.warning("Cache and query are empty and launch_queries has been called")
        return full_query, array_ordered_list

    @profile
    def launch_queries(self) -> None:
        # The code that query the request is inspired from https://github.com/mocnik-science/osm-python-tools
        # in the OSMPythonTools/internal/cacheObject.py file
        # Then we split the result into the multiple results and then process it as it is done with
        # overpy.Result. The second part of the code of this function used to process the results
        # comes from overpy.Overpass.from_json function and has been adapted to this situation with multiple results
        """Merge all queries into a single one, launch the query, get the results and process them."""
        if len(self.query_dict.keys()) == 0:
            return None

        logger.info("Downloading data from OSM API")
        query, array_ordered_list = self.merge_queries()
        with Profiling.Scope("Download overpass data"):
            endpoint = 'http://overpass-api.de/api/'
            request = urllib.request.Request(endpoint + 'interpreter',
                                             urllib.parse.urlencode({'data': query}).encode('utf-8'))
            agent = 'Pretty-gpx/ (https://github.com/ThomasParistech/pretty-gpx)'

            if not isinstance(request, urllib.request.Request):
                request = urllib.request.Request(request)
            request.headers['User-Agent'] = agent
            try:
                response = urllib.request.urlopen(request)
            except Exception as err:
                msg = "The requested data could not be downloaded. Please check whether your internet connection."
                logger.exception(msg)
                raise Exception(msg, err)

        with Profiling.Scope("Loading data into JSON"):
            content_bytes = response.read()
            logger.info(f"Downloaded {convert_bytes(len(content_bytes))}")
            data = ujson.loads(content_bytes)

        logger.info("Loading overpass data into overpy")
        with Profiling.Scope("Loading overpass data into overpy"):
            elem_cls: Area | Node | Relation | Way
            result_i = Result(elements=None,
                              api=Overpass())
            element_i: list[Area | Node | Relation | Way] = []
            i = 0
            for element in data.get("elements", []):
                e_type = element.get("type")
                if hasattr(e_type, "lower") and e_type.lower() == "count":
                    if len(element_i) > 0:
                        result_i.expand(Result(elements=element_i))
                    # Even if it is empty we should add the data
                    self.query_unprocessed_results[array_ordered_list[i]] = result_i
                    i += 1
                    result_i = Result(elements=None,
                                      api=Overpass())
                    element_i = []
                else:
                    for elem_cls in [Node, Way, Relation, Area]:
                        if hasattr(e_type, "lower") and e_type.lower() == elem_cls._type_value:
                            element_i.append(elem_cls.from_json(element, result=result_i))
            if len(element_i) > 0:
                result_i.expand(Result(elements=element_i))
            if i < len(array_ordered_list):
                self.query_unprocessed_results[array_ordered_list[i]] = result_i

    def is_cached(self,
                  array_name: str) -> bool:
        """Returns if the array has a cache file."""
        return array_name in self.query_cached_results

    def get_cache_file(self,
                       array_name: str) -> str:
        """Get the cache file path."""
        return self.query_cached_results[array_name]

    def get_query_result(self,
                         array_name: str) -> Result:
        """Get the query result (overpy.Result)."""
        if array_name not in self.query_unprocessed_results:
            raise KeyError(f"The specified array name ({array_name})"
                           "has not been added to the query/not been resolved")
        return self.query_unprocessed_results[array_name]


@profile
def overpass_query(query_elements: list[str],
                   bounds: GpxBounds | GpxTrack,
                   include_way_nodes: bool = False,
                   return_geometry: bool = False,
                   add_relative_margin: float | None = None,
                   max_retry_count: int = 2) -> Result:
    """Query the overpass API for a single request."""
    # See https://wiki.openstreetmap.org/wiki/Key:natural
    # See https://wiki.openstreetmap.org/wiki/Key:mountain_pass
    # See https://wiki.openstreetmap.org/wiki/Tag:tourism=alpine_hut
    api = Overpass(max_retry_count=max_retry_count)
    if isinstance(bounds, GpxTrack):
        bounds = bounds.get_bounds()

    if add_relative_margin is not None:
        bounds = bounds.add_relative_margin(add_relative_margin)

    bounds_str = f"({bounds.lat_min:.5f}, {bounds.lon_min:.5f}, {bounds.lat_max:.5f}, {bounds.lon_max:.5f})"

    query_body = "\n".join([f"{element}{bounds_str};" for element in query_elements])

    if return_geometry:
        out_param = "geom"
    else:
        out_param = "body"

    if include_way_nodes:
        recursion_param = "(._;>;);\n"
    else:
        recursion_param = ""

    query = f"""(
       {query_body}
    );
    {recursion_param}
    out {out_param};"""
    result = api.query(query)

    if DEBUG_OVERPASS_QUERY:
        logger.debug("----")
        logger.debug(f"GPX bounds: {bounds_str}")
        named_nodes = [node for node in result.nodes if "name" in node.tags]
        named_nodes.sort(key=lambda node: node.tags['name'])
        for node in named_nodes:
            logger.debug(f"{node.tags['name']} at ({node.lat:.3f}, {node.lon:.3f}) {node.tags}")
        logger.debug("----")

    return result
