#!/usr/bin/python3
"""Scatter Point."""
from collections import defaultdict
from dataclasses import dataclass
from enum import auto
from enum import Enum

from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.utils import get


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

    @staticmethod
    def log(points: list['ScatterPoint']) -> None:
        """Log the Scatter Points."""
        lines = ["Scatter Points:"]

        categories: dict[ScatterPointCategory, list[str]] = defaultdict(list)

        # Group points by category
        for point in points:
            categories[point.category].append(get(point.name, "?"))

        # Log the names for each category
        for category, names in categories.items():
            lines.append(f"- {category.name}: {', '.join(sorted(names))}")

        logger.info("\n".join(lines))

# TODO (upgrade): NMS based on a list of importance over the ScatterPointCategory
