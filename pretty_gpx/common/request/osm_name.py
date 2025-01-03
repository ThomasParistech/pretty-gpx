#!/usr/bin/python3
"""Name of OpenStreetMap elements."""


from overpy import Node
from overpy import Relation
from overpy import Way


def get_shortest_name(nwr: Node | Way | Relation) -> str | None:
    """Retrieve the shortest available name from OpenStreetMap tags (to ease text allocation)."""
    # https://www.openstreetmap.org/way/369161987
    # "name"      : St Paul's Cathedral
    # "short_name": Saint Paul's
    # "alt_name"  :	/
    # "wikipedia" : en:St Paul's Cathedral
    #
    # https://www.openstreetmap.org/way/201611261
    # "name"      : Cathédrale Notre-Dame de Paris
    # "short_name": Notre-Dame
    # "alt_name"  :	Notre-Dame de Paris
    # "wikipedia" : fr:Cathédrale Notre-Dame de Paris
    #
    # https://www.openstreetmap.org/relation/3374550
    # "name"      : The Monument to the Great Fire of London
    # "short_name": /
    # "alt_name"  : The Monument
    # "wikipedia" : en:Monument to the Great Fire of London
    #
    # https://www.openstreetmap.org/way/19856722#map=19/48.862817/2.342818
    # "name"      : Bourse de Commerce — Pinault Collection
    # "short_name": /
    # "alt_name"  :	/
    # "wikipedia" : fr:Bourse de commerce de Paris
    #
    # https://www.openstreetmap.org/relation/65066
    # "name"      : Massachusetts Institute of Technology
    # "short_name": MIT
    # "alt_name"  :	/
    # "wikipedia" : en:Massachusetts Institute of Technology
    #
    # https://www.openstreetmap.org/way/54519165
    # "name"      : National University of Singapore
    # "short_name": NUS
    # "alt_name"  :	/
    # "wikipedia" : en:National University of Singapore
    #
    # https://www.openstreetmap.org/way/56131470
    # "name"      : École normale supérieure - Université PSL
    # "short_name": ENS
    # "alt_name"  :	École normale supérieure;Ulm;ENS Ulm;Normale sup';Normale sup' Ulm;ENS Campus d'Ulm
    # "wikipedia" : fr:École normale supérieure (Paris)

    tags = nwr.tags
    if tags is None:
        return None

    possible_names: list[str] = []
    name = tags.get("name", None)
    if name is not None:
        possible_names.append(str(name))

    short_name = tags.get("short_name", None)
    if short_name is not None:
        possible_names.append(str(short_name))

    wikipedia = tags.get("wikipedia", None)
    if wikipedia is not None:
        wiki_name = str(wikipedia).split(":", 1)[1]
        possible_names.append(wiki_name)

    alt_names = tags.get("alt_name", None)
    if alt_names is not None:
        possible_names.extend(str(alt_names).split(";"))

    if len(possible_names) == 0:
        return None

    return min(possible_names, key=len)
