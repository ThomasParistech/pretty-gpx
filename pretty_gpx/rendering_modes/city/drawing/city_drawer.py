#!/usr/bin/python3
"""Drawing a City Poster from a single GPX file."""
from dataclasses import dataclass

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pretty_gpx.common.data.place_name import get_start_end_named_points
from pretty_gpx.common.drawing.components.annotated_scatter import AnnotatedScatterAll
from pretty_gpx.common.drawing.components.centered_title import CenteredTitle
from pretty_gpx.common.drawing.components.elevation_profile import ElevationProfile
from pretty_gpx.common.drawing.components.track_data import TrackData
from pretty_gpx.common.drawing.utils.drawer import DrawerSingleTrack
from pretty_gpx.common.drawing.utils.drawing_figure import DrawingFigure
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.layout.vertical_layout import VerticalLayoutUnion
from pretty_gpx.common.request.overpass_request import OverpassQuery
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import profile_parallel
from pretty_gpx.rendering_modes.city.data.bridges import prepare_download_city_bridges
from pretty_gpx.rendering_modes.city.data.bridges import process_city_bridges
from pretty_gpx.rendering_modes.city.data.city_pois import prepare_download_city_pois
from pretty_gpx.rendering_modes.city.data.city_pois import process_city_pois
from pretty_gpx.rendering_modes.city.drawing.city_background import CityBackground
from pretty_gpx.rendering_modes.city.drawing.city_params import CityParams


@dataclass
class CityLayout:
    """Vertical Layout of the City Poster."""
    layouts: VerticalLayoutUnion
    background: CityBackground
    bot: ElevationProfile
    top: CenteredTitle
    mid_scatter: AnnotatedScatterAll
    mid_track: TrackData

    paper: PaperSize


@dataclass(kw_only=True)
class CityDrawer(DrawerSingleTrack):
    """Class drawing a City Poster from a single GPX file."""
    top_ratio: float
    bot_ratio: float
    margin_ratio: float

    params: CityParams

    data: CityLayout | None = None

    @profile
    def change_gpx(self, gpx_path: str | bytes, paper: PaperSize) -> None:
        """Load a single GPX file to create a City Poster."""
        gpx_track = GpxTrack.load(gpx_path)
        layouts = VerticalLayoutUnion.from_track(gpx_track,
                                                 top_ratio=self.top_ratio,
                                                 bot_ratio=self.bot_ratio,
                                                 margin_ratio=self.margin_ratio)

        total_query = OverpassQuery()
        prepare_download_city_bridges(total_query, gpx_track)
        prepare_download_city_pois(total_query, gpx_track)
        total_query.launch_queries()

        scatter_points = get_start_end_named_points(gpx_track)
        scatter_points += process_city_bridges(total_query, gpx_track)
        scatter_points += process_city_pois(total_query, gpx_track)
        # TODO(upgrade): Draw the POIs as well. This is currently disabled because text allocation fails when there
        # are too many overlapping scatter points. Need to filter out the points that are too close to each other.
        background = CityBackground.from_union_bounds(layouts.union_bounds, self.params.user_road_precision)

        layout = layouts.layouts[paper]
        background.change_papersize(paper, layout.background_bounds)
        ele_pofile = ElevationProfile.from_track(layout.bot_bounds, gpx_track, scatter_points, ele_ratio=0.45)
        title = CenteredTitle(bounds=layout.top_bounds)
        scatter_all = AnnotatedScatterAll.from_scatter(paper, layout.background_bounds, layout.mid_bounds,
                                                       scatter_points, self.params)
        track_data = TrackData.from_track(gpx_track)

        self.data = CityLayout(layouts=layouts,
                               background=background,
                               bot=ele_pofile,
                               top=title,
                               mid_scatter=scatter_all,
                               mid_track=track_data,
                               paper=paper)

    @profile
    def update_background(self, paper: PaperSize) -> None:
        """Update the background (for example when road priority changes)."""
        assert self.data is not None
        gpx_track = self.data.mid_track.track
        assert isinstance(gpx_track, GpxTrack)
        layouts = VerticalLayoutUnion.from_track(gpx_track,
                                                 top_ratio=self.top_ratio,
                                                 bot_ratio=self.bot_ratio,
                                                 margin_ratio=self.margin_ratio)

        background = CityBackground.from_union_bounds(layouts.union_bounds, self.params.user_road_precision)
        layout = layouts.layouts[paper]
        background.change_papersize(paper, layout.background_bounds)
        self.data.background = background

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
            self.data.background.draw(f, self.params)
            self.data.bot.draw(f, self.params)
            self.data.top.draw(f, self.params)
            self.data.mid_track.draw(f, self.params)
            self.data.mid_scatter.draw(f, self.params)

@profile_parallel
def _update_city_background(drawer: CityDrawer, paper: PaperSize) -> CityDrawer:
    """Process the GPX file and return the new drawer."""
    # This function is designed for parallel execution and will be pickled.
    # Defining it as a global function avoids pickling the entire UiManager class,
    # which contains non-picklable elements like local lambdas and UI components.
    assert isinstance(drawer, DrawerSingleTrack)
    drawer.update_background(paper)
    return drawer
