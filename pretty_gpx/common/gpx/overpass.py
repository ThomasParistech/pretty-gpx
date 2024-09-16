#!/usr/bin/python3
"""Overpass API."""

import overpy

from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.utils.logger import logger

DEBUG_OVERPASS_QUERY = False


def overpass_query(query_elements: list[str],
                   bounds: GpxBounds | GpxTrack,
                   include_way_nodes: bool = False) -> overpy.Result:
    """Query the overpass API."""
    # See https://wiki.openstreetmap.org/wiki/Key:natural
    # See https://wiki.openstreetmap.org/wiki/Key:mountain_pass
    # See https://wiki.openstreetmap.org/wiki/Tag:tourism=alpine_hut
    api = overpy.Overpass()
    if isinstance(bounds, GpxTrack):
        bounds = GpxBounds.from_list(list_lon=bounds.list_lon,
                                     list_lat=bounds.list_lat)

    bounds = bounds.add_relative_margin(0.1)

    bounds_str = f"({bounds.lat_min:.5f}, {bounds.lon_min:.5f}, {bounds.lat_max:.5f}, {bounds.lon_max:.5f})"

    query_body = "\n".join([f"{element}{bounds_str};" for element in query_elements])
    if include_way_nodes:
        query_body += "\n>;\n"

    query = f"""(
       {query_body}
    );
    out body;"""
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
