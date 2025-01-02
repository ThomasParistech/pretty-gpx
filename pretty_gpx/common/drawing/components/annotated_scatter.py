#!/usr/bin/python3
"""Drawing Component for Annotated Scatter."""
from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol

from matplotlib.font_manager import FontProperties

from pretty_gpx.common.drawing.utils.drawing_figure import A4Float
from pretty_gpx.common.drawing.utils.drawing_figure import DrawingFigure
from pretty_gpx.common.drawing.utils.plt_marker import MarkerType
from pretty_gpx.common.drawing.utils.scatter_point import ScatterPoint
from pretty_gpx.common.drawing.utils.scatter_point import ScatterPointCategory
from pretty_gpx.common.drawing.utils.text_allocation import allocate_text
from pretty_gpx.common.drawing.utils.text_allocation import TextAllocationInput
from pretty_gpx.common.drawing.utils.text_allocation import TextAllocationOutput
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.asserts import assert_eq
from pretty_gpx.common.utils.asserts import assert_in
from pretty_gpx.common.utils.asserts import assert_same_len
from pretty_gpx.common.utils.utils import safe


@dataclass
class ScatterParams:
    """Scatter Parameters."""
    markersize: A4Float
    marker: MarkerType
    color: str


class ScatterAllParamsProtocol(Protocol):
    """Protocol for Scatter Parameters."""
    @property
    def scatter_params(self) -> dict[ScatterPointCategory, ScatterParams]: ...  # noqa: D102


@dataclass
class AnnotationArrow:
    """Annotation Arrow."""
    text_s: str
    text_lat: float
    text_lon: float
    arrow_begin_lat: float
    arrow_begin_lon: float


@dataclass
class AnnotatedScatterParams:
    """Parameters for Annotated Scatter."""
    arrow_linewidth: A4Float
    fontsize: A4Float


class AnnotatedScatterAllParamsProtocol(ScatterAllParamsProtocol, Protocol):
    """Protocol for Annotated Scatter Parameters."""
    @property
    def annot_params(self) -> dict[ScatterPointCategory, AnnotatedScatterParams]: ...  # noqa: D102

    annot_fontproperties: FontProperties
    annot_ha: str
    annot_va: str


@dataclass
class AnnotatedScatter:
    """Annotated Scatter."""
    paper_size: PaperSize
    list_lat: list[float]
    list_lon: list[float]
    annotations: list[AnnotationArrow | None]


@dataclass
class AnnotatedScatterAll:
    """Annotated Scatter All."""
    scatters: dict[ScatterPointCategory, AnnotatedScatter]
    background_bounds: GpxBounds

    @staticmethod
    def from_scatter(paper_size: PaperSize,
                     background_bounds: GpxBounds,
                     mid_bounds: GpxBounds,
                     points: list[ScatterPoint],
                     params: AnnotatedScatterAllParamsProtocol) -> 'AnnotatedScatterAll':
        """Initialize Annotated Scatter All."""
        input = setup_text_allocation(paper_size, points, params)
        output = allocate_text(input, paper_size, background_bounds, mid_bounds)
        scatters = finalize_text_allocation(paper_size, points, input, output)
        return AnnotatedScatterAll(scatters, background_bounds)

    def change_papersize(self, paper: PaperSize, bounds: GpxBounds, params: AnnotatedScatterAllParamsProtocol) -> None:
        """Change Paper Size and GPX Bounds."""
        # Unlike other components, we need the parameters to change the paper size, since we reallocate the text
        points = [ScatterPoint(name=None if annot is None else annot.text_s, lat=lat, lon=lon, category=category)
                  for category, scatter in self.scatters.items()
                  for lat, lon, annot in zip(scatter.list_lat, scatter.list_lon, scatter.annotations)]
        self.scatters = AnnotatedScatterAll.from_scatter(paper, self.background_bounds, bounds,
                                                         points, params).scatters

    def draw(self, fig: DrawingFigure, params: AnnotatedScatterAllParamsProtocol) -> None:
        """Draw the Scatter points with annotations."""
        for category, scatter in self.scatters.items():
            assert_in(category, params.annot_params)
            assert_in(category, params.scatter_params)
            annot_params = params.annot_params[category]
            scatter_params = params.scatter_params[category]

            assert_eq(scatter.paper_size.name, fig.paper_size.name)
            fig.scatter(list_lat=scatter.list_lat, list_lon=scatter.list_lon, color=scatter_params.color,
                        marker=scatter_params.marker, markersize=scatter_params.markersize)

            for idx, ann in enumerate(scatter.annotations):
                if ann is not None:
                    fig.arrow_to_marker(begin_lat=ann.arrow_begin_lat, begin_lon=ann.arrow_begin_lon,
                                        marker_lat=scatter.list_lat[idx], marker_lon=scatter.list_lon[idx],
                                        marker_size=scatter_params.markersize, color=scatter_params.color,
                                        lw=annot_params.arrow_linewidth)
                    fig.text(lon=ann.text_lon, lat=ann.text_lat, s=ann.text_s,
                             color=scatter_params.color,
                             fontsize=annot_params.fontsize,
                             font=params.annot_fontproperties,
                             ha=params.annot_ha, va=params.annot_va)


def setup_text_allocation(paper_size: PaperSize,
                          points: list[ScatterPoint],
                          params: AnnotatedScatterAllParamsProtocol) -> TextAllocationInput:
    """Setup Text Allocation."""
    input = TextAllocationInput(annot_fontproperties=params.annot_fontproperties,
                                annot_ha=params.annot_ha,
                                annot_va=params.annot_va)
    for scatter in points:
        assert_in(scatter.category, params.annot_params)
        assert_in(scatter.category, params.scatter_params)
        annot_params = params.annot_params[scatter.category]
        scatter_params = params.scatter_params[scatter.category]
        input.scatters_to_avoid_x.append(scatter.lon)
        input.scatters_to_avoid_y.append(scatter.lat)
        input.scatter_to_avoid_sizes.append(scatter_params.markersize(paper_size))
        # TODO (upgrade): Make sure we use the correct size. Because scatter and plot sizes are different

        if scatter.name is not None:
            input.list_text_x.append(scatter.lon)
            input.list_text_y.append(scatter.lat)
            input.list_text_s.append(scatter.name)
            input.list_text_size.append(annot_params.fontsize(paper_size))
    return input


def finalize_text_allocation(paper_size: PaperSize,
                             points: list[ScatterPoint],
                             input: TextAllocationInput,
                             output: TextAllocationOutput) -> dict[ScatterPointCategory, AnnotatedScatter]:
    """Finalize Text Allocation."""
    assert_same_len((output.texts_xy, output.lines_xy, input.list_text_s))

    res: dict[ScatterPointCategory, AnnotatedScatter] = defaultdict(lambda: AnnotatedScatter(paper_size=paper_size,
                                                                                             list_lat=[],
                                                                                             list_lon=[],
                                                                                             annotations=[]))
    alloc_idx = 0
    for scatter in points:
        annot = None
        if scatter.name is not None:
            text, line = output.texts_xy[alloc_idx], output.lines_xy[alloc_idx]
            text_x, text_y = safe(text)
            line_x, line_y = safe(line)
            annot = AnnotationArrow(text_s=input.list_text_s[alloc_idx],
                                    text_lat=text_y,
                                    text_lon=text_x,
                                    arrow_begin_lat=line_y[0],
                                    arrow_begin_lon=line_x[0])
            alloc_idx += 1

        res[scatter.category].list_lat.append(scatter.lat)
        res[scatter.category].list_lon.append(scatter.lon)
        res[scatter.category].annotations.append(annot)

    return dict(res)
