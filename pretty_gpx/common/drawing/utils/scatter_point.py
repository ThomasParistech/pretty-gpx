#!/usr/bin/python3
"""Scatter Point."""
from dataclasses import dataclass
from enum import auto
from enum import Enum


class ScatterPointCategory(Enum):
    """Scatter Point Category."""
    MOUNTAIN_PASS = auto()
    MOUNTAIN_HUT = auto()
    CITY_BRIDGE = auto()
    CITY_POI_GREAT = auto()
    CITY_POI_DEFAULT = auto()
    START = auto()
    END = auto()


@dataclass(kw_only=True)
class ScatterPoint:
    """Scatter Point."""
    name: str | None
    lat: float
    lon: float
    category: ScatterPointCategory

# TODO (upgrade): NMS based on a list of importance over the ScatterPointCategory
