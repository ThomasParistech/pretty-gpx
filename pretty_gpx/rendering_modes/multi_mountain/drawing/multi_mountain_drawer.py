#!/usr/bin/python3
"""Drawing a Multi Mountain Poster from several GPX files."""
from dataclasses import dataclass

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pretty_gpx.common.data.place_name import get_start_end_named_points
from pretty_gpx.common.drawing.components.annotated_scatter import AnnotatedScatterAll
from pretty_gpx.common.drawing.components.centered_title import CenteredTitle
from pretty_gpx.common.drawing.components.elevation_profile import ElevationProfile
from pretty_gpx.common.drawing.components.track_data import TrackData
from pretty_gpx.common.drawing.utils.drawer import DrawerMultiTrack
from pretty_gpx.common.drawing.utils.drawing_figure import DrawingFigure
from pretty_gpx.common.gpx.multi_gpx_track import MultiGpxTrack
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.layout.vertical_layout import VerticalLayoutUnion
from pretty_gpx.common.request.overpass_request import OverpassQuery
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.rendering_modes.mountain.drawing.mountain_background import MountainBackground
from pretty_gpx.rendering_modes.multi_mountain.data.mountain_huts import prepare_download_mountain_huts
from pretty_gpx.rendering_modes.multi_mountain.data.mountain_huts import process_mountain_huts
from pretty_gpx.rendering_modes.multi_mountain.drawing.multi_mountain_params import MultiMountainParams


@dataclass
class MultiMountainLayout:
    """Vertcal Layout of the Mountain Poster."""
    layouts: VerticalLayoutUnion
    background: MountainBackground
    bot: ElevationProfile
    top: CenteredTitle
    mid_scatter: AnnotatedScatterAll
    mid_track: TrackData

    paper: PaperSize


@dataclass(kw_only=True)
class MultiMountainDrawer(DrawerMultiTrack):
    """Class drawing a Mountain Poster from a single GPX file."""
    top_ratio: float
    bot_ratio: float
    margin_ratio: float

    params: MultiMountainParams

    data: MultiMountainLayout | None = None

    @profile
    def change_gpx(self, gpx_paths: list[str] | list[bytes], paper: PaperSize) -> None:
        """Load several GPX file to create a Multi Mountain Poster."""
        gpx_track = MultiGpxTrack.load(gpx_paths)
        layouts = VerticalLayoutUnion.from_track(gpx_track,
                                                 top_ratio=self.top_ratio,
                                                 bot_ratio=self.bot_ratio,
                                                 margin_ratio=self.margin_ratio)

        total_query = OverpassQuery()
        prepare_download_mountain_huts(total_query, gpx_track)
        total_query.launch_queries()

        scatter_points = get_start_end_named_points(gpx_track)
        scatter_points += process_mountain_huts(total_query, gpx_track)
        background = MountainBackground.from_union_bounds(layouts.union_bounds)

        layout = layouts.layouts[paper]
        background.change_papersize(paper, layout.background_bounds)
        ele_profile = ElevationProfile.from_track(layout.bot_bounds, gpx_track.merge(), scatter_points, ele_ratio=0.45)
        title = CenteredTitle(bounds=layout.top_bounds)
        scatter_all = AnnotatedScatterAll.from_scatter(paper, layout.background_bounds, layout.mid_bounds,
                                                       scatter_points, self.params)
        track_data = TrackData.from_track(gpx_track)

        self.data = MultiMountainLayout(layouts=layouts,
                                        background=background,
                                        bot=ele_profile,
                                        top=title,
                                        mid_scatter=scatter_all,
                                        mid_track=track_data,
                                        paper=paper)

    @profile
    def change_papersize(self, paper: PaperSize) -> None:
        """Change Papersize of the poster."""
        assert self.data is not None

        if self.data.paper == paper:
            return

        layout = self.data.layouts.layouts[paper]
        self.data.paper = paper
        self.data.background.change_papersize(paper, layout.background_bounds)
        self.data.bot.change_papersize(paper, layout.bot_bounds)
        self.data.top.change_papersize(paper, layout.top_bounds)
        self.data.mid_scatter.change_papersize(paper, layout.mid_bounds, self.params)
        self.data.mid_track.change_papersize(paper, layout.mid_bounds)

    @profile
    def draw(self, fig: Figure, ax: Axes, high_resolution: bool) -> None:
        """Draw the poster on the given figure and axes (in high resolution if requested)."""
        assert self.data is not None
        with DrawingFigure(self.data.paper, self.data.layouts.layouts[self.data.paper].background_bounds, fig, ax) as f:
            self.data.background.draw(f, self.params, high_resolution)
            self.data.bot.draw(f, self.params)
            self.data.top.draw(f, self.params)
            self.data.mid_track.draw(f, self.params)
            self.data.mid_scatter.draw(f, self.params)
