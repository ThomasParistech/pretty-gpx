#!/usr/bin/python3
"""Text Allocation."""
from dataclasses import dataclass
from dataclasses import field

import matplotlib
import matplotlib.pyplot as plt
import textalloc as ta
from matplotlib.font_manager import FontProperties

from pretty_gpx.common.drawing.utils.drawing_figure import A4Float
from pretty_gpx.common.drawing.utils.drawing_figure import DrawingFigure
from pretty_gpx.common.drawing.utils.plt_marker import MarkerType
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.asserts import assert_len
from pretty_gpx.common.utils.asserts import assert_same_len
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.plt import MatplotlibBackend
from pretty_gpx.common.utils.profile import profile

DEBUG = False


@dataclass(kw_only=True)
class TextAllocationInput:
    """Input of textalloc."""
    annot_fontproperties: FontProperties
    annot_ha: str
    annot_va: str

    scatters_to_avoid_x: list[float] = field(default_factory=list)
    scatters_to_avoid_y: list[float] = field(default_factory=list)
    scatter_to_avoid_sizes: list[float] = field(default_factory=list)
    list_text_x: list[float] = field(default_factory=list)
    list_text_y: list[float] = field(default_factory=list)
    list_text_s: list[str] = field(default_factory=list)
    list_text_size: list[float] = field(default_factory=list)


@dataclass(kw_only=True)
class TextAllocationOutput:
    """Output of textalloc."""
    texts_xy: list[tuple[float, float]] = field(default_factory=list)
    lines_xy: list[tuple[tuple[float, float], tuple[float, float]]] = field(default_factory=list)


@profile
def allocate_text(input: TextAllocationInput,
                  paper_size: PaperSize,
                  background_bounds: GpxBounds,
                  mid_bounds: GpxBounds,
                  min_distance: float = 0.04,  # TODO (upgrade): make this ths paper or scale dependent ?
                  max_distance: float = 0.2,
                  margin: float = 0.008,
                  nbr_candidates: int = 300) -> TextAllocationOutput:
    """Call textalloc and surround it with debug plots."""
    if DEBUG:
        __debug_before(paper_size, background_bounds, mid_bounds, input)

    matplotlib.use('Agg')
    fig, ax = plt.subplots()

    with DrawingFigure(paper_size, background_bounds, fig, ax):
        logger.info(f"Optimize {len(input.list_text_s)} Text Allocations...")
        texts_xyz, lines_xyz, _, _ = ta.allocate(ax,
                                                 x=input.list_text_x,
                                                 y=input.list_text_y,
                                                 text_list=input.list_text_s,
                                                 textsize=input.list_text_size,
                                                 xlims=(mid_bounds.lon_min, mid_bounds.lon_max),
                                                 ylims=(mid_bounds.lat_min, mid_bounds.lat_max),
                                                 # x_lines=None,
                                                 # y_lines=None,
                                                 x_scatter=input.scatters_to_avoid_x,
                                                 y_scatter=input.scatters_to_avoid_y,
                                                 scatter_sizes=input.scatter_to_avoid_sizes,  # type: ignore
                                                 max_distance=max_distance,
                                                 min_distance=min_distance,
                                                 margin=margin,
                                                 nbr_candidates=nbr_candidates,
                                                 # linewidth=output_linewidth,
                                                 draw_lines=True,
                                                 draw_all=False,
                                                 priority_strategy="largest",
                                                 avoid_label_lines_overlap=True,
                                                 avoid_crossing_label_lines=True,
                                                 ha=input.annot_ha,
                                                 va=input.annot_va,
                                                 fontproperties=input.annot_fontproperties)
    output = TextAllocationOutput()
    assert_same_len((texts_xyz, lines_xyz, input.list_text_s))
    for text, line in zip(texts_xyz, lines_xyz):
        assert text is not None, "Failed to allocate text"
        assert_len(text, 3)
        text_x, text_y, _ = text

        assert line is not None
        assert_len(line, 3)
        line_x, line_y, _ = line
        assert_len(line_x, 2)
        assert_len(line_y, 2)

        output.texts_xy.append((text_x, text_y))
        output.lines_xy.append((line_x, line_y))

    if DEBUG:
        __debug_after(paper_size, background_bounds, mid_bounds, input, output)

    logger.info("Succesful Text Allocation")

    return output


def __debug_before(paper_size: PaperSize,
                   background_bounds: GpxBounds,
                   mid_bounds: GpxBounds,
                   input: TextAllocationInput) -> None:
    with MatplotlibBackend('TkAgg'):
        debug_fig, debug_ax = plt.subplots()
        with DrawingFigure(paper_size, background_bounds, debug_fig, debug_ax) as debug_f:
            debug_f.rectangle(bounds=background_bounds, color="green", lw=A4Float(mm=0.5))
            debug_f.rectangle(bounds=mid_bounds, color="blue", lw=A4Float(mm=0.5))

            debug_f.scatter(list_lat=input.scatters_to_avoid_y, list_lon=input.scatters_to_avoid_x, color="red",
                            marker=MarkerType.DISK,
                            markersize=A4Float(mm=3))
            for text_x, text_y, text_s, fsize in zip(input.list_text_x, input.list_text_y, input.list_text_s,
                                                     input.list_text_size):
                debug_ax.text(text_x, text_y, text_s, ha="center", va="center",
                              fontsize=fsize, fontproperties=input.annot_fontproperties)
            plt.title(f"{len(input.list_text_s)} Texts to Allocate")
            plt.show()


def __debug_after(paper_size: PaperSize,
                  background_bounds: GpxBounds,
                  mid_bounds: GpxBounds,
                  input: TextAllocationInput,
                  output: TextAllocationOutput) -> None:
    with MatplotlibBackend('TkAgg'):
        debug_fig, debug_ax = plt.subplots()
        with DrawingFigure(paper_size, background_bounds, debug_fig, debug_ax) as debug_f:
            debug_f.rectangle(bounds=background_bounds, color="green", lw=A4Float(mm=0.5))
            debug_f.rectangle(bounds=mid_bounds, color="blue", lw=A4Float(mm=0.5))

            debug_f.scatter(list_lat=input.scatters_to_avoid_y, list_lon=input.scatters_to_avoid_x, color="red",
                            marker=MarkerType.DISK,
                            markersize=A4Float(mm=3))
            for text, line, text_s, fsize in zip(output.texts_xy, output.lines_xy, input.list_text_s,
                                                 input.list_text_size):
                text_x, text_y = text
                line_x, line_y = line
                debug_ax.plot(line_x, line_y, ":m")
                debug_ax.text(text_x, text_y, text_s, ha="center", va="center",
                              fontsize=fsize, fontproperties=input.annot_fontproperties)
            plt.title(f"{len(input.list_text_s)} Texts to Allocate")
            plt.show()
