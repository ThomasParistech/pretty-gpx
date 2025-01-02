#!/usr/bin/python3
"""Multi Gpx Track."""
from dataclasses import dataclass
from dataclasses import field

from shapely.geometry import LineString

from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_distance import get_distance_m
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.utils.asserts import assert_ge
from pretty_gpx.common.utils.asserts import assert_not_empty


@dataclass
class MultiGpxTrack:
    """Multi Gpx Track."""
    tracks: list[GpxTrack] = field(default_factory=list)

    def __post_init__(self) -> None:
        assert_ge(len(self.tracks), 2)

        for i in range(len(self) - 1):
            crt_track = self.tracks[i]
            next_track = self.tracks[i+1]
            distance_m = get_distance_m(lonlat_1=(crt_track.list_lon[-1], crt_track.list_lat[-1]),
                                        lonlat_2=(next_track.list_lon[0], next_track.list_lat[0]))
            if distance_m > 500:
                raise AssertionError("Too large gap between consecutive GPX tracks. "
                                     "Check the alphabetical order of the files. "
                                     "Or edit the GPX files manually.")

    def __len__(self) -> int:
        return len(self.tracks)

    @staticmethod
    def load(list_gpx_path: list[str] | list[bytes] | list[str | bytes]) -> 'MultiGpxTrack':
        """Load multiple GPX files and return MultiGpxTrack."""
        tracks = [GpxTrack.load(path) for path in list_gpx_path]

        return MultiGpxTrack(tracks=tracks)

    def merge(self) -> GpxTrack:
        """Merge multiple GpxTrack into one."""
        assert_not_empty(self.tracks)

        list_cumul_d = self.tracks[0].list_cumul_dist_km
        for gpx in self.tracks[1:]:
            list_cumul_d.extend([cumul_d + list_cumul_d[-1] for cumul_d in gpx.list_cumul_dist_km])

        durations = [gpx.duration_s for gpx in self.tracks if gpx.duration_s is not None]
        total_duration = sum(durations) if len(durations) == len(self.tracks) else None

        return GpxTrack(list_lon=[lon
                                  for gpx in self.tracks
                                  for lon in gpx.list_lon],
                        list_lat=[lat
                                  for gpx in self.tracks
                                  for lat in gpx.list_lat],
                        list_ele_m=[ele
                                    for gpx in self.tracks
                                    for ele in gpx.list_ele_m],
                        list_cumul_dist_km=list_cumul_d,
                        uphill_m=sum(gpx.uphill_m for gpx in self.tracks),
                        duration_s=total_duration)

    def get_bounds(self) -> GpxBounds:
        """Get the bounds of the track."""
        return GpxBounds.union([gpx.get_bounds() for gpx in self.tracks])

    def get_transitions(self) -> list[LineString]:
        """Get the transitions between the tracks."""
        return [LineString([(gpx.list_lon[0], gpx.list_lat[0]),
                            (gpx.list_lon[-1], gpx.list_lat[-1])])
                for gpx in self.tracks]
