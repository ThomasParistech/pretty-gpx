"""City Road Types."""

from dataclasses import dataclass
from enum import auto
from enum import Enum


class CityRoadType(Enum):
    """City Road Type."""
    HIGHWAY = auto()
    SECONDARY_ROAD = auto()
    STREET = auto()
    ACCESS_ROAD = auto()


@dataclass(frozen=True)
class RoadTypeData:
    """Data for each type of city road."""
    tags: list[str]
    priority: int
    query_name: str

# Dictionary of RoadTypeData for each CityRoadType, ordered by priority
ROAD_TYPE_DATA: dict[CityRoadType, RoadTypeData] = {
    CityRoadType.HIGHWAY: RoadTypeData(tags=["motorway", "trunk", "primary"], priority=0, query_name="highway"),
    CityRoadType.SECONDARY_ROAD: RoadTypeData(tags=["tertiary", "secondary"], priority=1, query_name="secondary_roads"),
    CityRoadType.STREET: RoadTypeData(tags=["residential", "living_street"], priority=2, query_name="street"),
    CityRoadType.ACCESS_ROAD: RoadTypeData(tags=["unclassified", "service"], priority=3, query_name="access_roads")
}

# Automatically check that ROAD_TYPE_DATA is sorted by priority
assert list(ROAD_TYPE_DATA.keys()) == sorted(ROAD_TYPE_DATA.keys(),
                                             key=lambda road_type: ROAD_TYPE_DATA[road_type].priority)


def get_city_roads_with_priority_better_than(x: int) -> list[CityRoadType]:
    """Returns a list of CityRoadType with a priority better than the given x."""
    # Filter ROAD_TYPE_DATA to get only those with priority less than x
    return [road_type for road_type, data in ROAD_TYPE_DATA.items() if data.priority < x]