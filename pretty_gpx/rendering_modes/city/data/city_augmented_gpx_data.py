#!/usr/bin/python3
"""City Augmented GPX Data."""
from dataclasses import dataclass
from typing import Final

from pretty_gpx.common.data.place_name import get_place_name
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.structure import AugmentedGpxData
from pretty_gpx.common.utils.profile import profile

LOOSE_THS_M: Final[float] = 1000


@dataclass
class CityAugmentedGpxData(AugmentedGpxData):
    """Class storing the GPX track augmented with names of start/end points."""
    track: GpxTrack

    start_name: str
    end_name: str | None

    is_closed: bool

    @property
    def dist_km(self) -> float:
        """Total distance in km."""
        return self.track.list_cumul_dist_km[-1]

    @property
    def uphill_m(self) -> float:
        """Total climb in m."""
        return self.track.uphill_m

    @property
    def duration_s(self) -> float | None:
        """Total duration in s."""
        return self.track.duration_s

    @profile
    @staticmethod
    def from_path(gpx_path: str | bytes) -> 'CityAugmentedGpxData':
        """Create an AugmentedGpxData instance from a GPX file."""
        gpx_track = GpxTrack.load(gpx_path)

        is_closed = gpx_track.is_closed(LOOSE_THS_M)

        start_name = get_place_name(lon=gpx_track.list_lon[0], lat=gpx_track.list_lat[0])

        if is_closed:
            end_name = None
        else:
            end_name = get_place_name(lon=gpx_track.list_lon[-1], lat=gpx_track.list_lat[-1])

        return CityAugmentedGpxData(track=gpx_track,
                                    start_name=start_name,
                                    end_name=end_name,
                                    is_closed=is_closed)
