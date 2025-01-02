#!/usr/bin/python3
"""Drawing Component for a GPX Track."""
from dataclasses import dataclass
from typing import Protocol

from pretty_gpx.common.drawing.utils.drawing_figure import A4Float
from pretty_gpx.common.drawing.utils.drawing_figure import DrawingFigure
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.gpx.multi_gpx_track import MultiGpxTrack
from pretty_gpx.common.layout.paper_size import PaperSize


class TrackParamsProtocol(Protocol):
    """Protocol for Track Parameters."""
    track_lw: A4Float
    track_color: str


@dataclass
class TrackData:
    """Drawing Component for a GPX Track."""
    track: GpxTrack | MultiGpxTrack

    @staticmethod
    def from_track(track: GpxTrack | MultiGpxTrack) -> 'TrackData':
        """Initialize the Track Data from the GPX Track."""
        return TrackData(track=track)

    def change_papersize(self, paper: PaperSize, bounds: GpxBounds) -> None:
        """Change Paper Size and GPX Bounds."""
        pass

    def draw(self, fig: DrawingFigure, params: TrackParamsProtocol) -> None:
        """Draw the GPX track."""
        tracks = [self.track] if isinstance(self.track, GpxTrack) else self.track.tracks
        for t in tracks:
            fig.polyline(list_lon=t.list_lon, list_lat=t.list_lat, color=params.track_color, lw=params.track_lw)
