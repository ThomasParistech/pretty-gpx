#!/usr/bin/python3
"""Text Allocation."""
import os
from dataclasses import dataclass
from dataclasses import field

import matplotlib.pyplot as plt
import textalloc as ta
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path

from pretty_gpx.common.drawing.base_drawing_figure import BaseDrawingFigure
from pretty_gpx.common.drawing.drawing_data import PlotData
from pretty_gpx.common.drawing.drawing_data import ScatterData
from pretty_gpx.common.drawing.drawing_data import TextData
from pretty_gpx.common.utils.asserts import assert_len
from pretty_gpx.common.utils.asserts import assert_same_len
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.paths import DATA_DIR
from pretty_gpx.common.utils.profile import profile

DEBUG_TEXT_ALLOCATION = False


@profile
def allocate_text(fig: Figure,
                  ax: Axes,
                  base_fig: BaseDrawingFigure,
                  scatters: 'AnnotatedScatterDataCollection',
                  plots_x_to_avoid: list[list[float]],
                  plots_y_to_avoid: list[list[float]],
                  fontsize: float,
                  fontproperties: FontProperties,
                  output_linewidth: float,
                  min_distance: float = 0.04,
                  max_distance: float = 0.2,
                  margin: float = 0.008,
                  nbr_candidates: int = 300,
                  ha: str = 'center',
                  va: str = 'center') -> tuple[list[TextData], list[PlotData]]:
    """Allocate text-boxes in imshow plot while avoiding overlap with other annotations."""
    base_fig.setup(fig, ax)

    logger.info(f"Optimize {len(scatters.list_text_x)} Text Allocations...")

    if DEBUG_TEXT_ALLOCATION:
        debug_fig, debug_ax = plt.subplots()
        base_fig.setup(debug_fig, debug_ax)
        debug_fig.set_dpi(600 / debug_fig.get_size_inches()[0])
        for list_x, list_y in zip(plots_x_to_avoid, plots_y_to_avoid):
            debug_ax.plot(list_x, list_y, "-r")
        for text_x, text_y, text_s in zip(scatters.list_text_x, scatters.list_text_y, scatters.list_text_s):
            debug_ax.text(text_x, text_y, text_s, ha="center", va="center",
                          fontsize=fontsize, fontproperties=fontproperties)
        plt.title("Texts to Allocate")
        plt.savefig(os.path.join(DATA_DIR, "text_before.svg"))
        plt.show()

    result_text_xy, result_line, _, _ = ta.allocate(ax,
                                                    x=scatters.list_text_x,
                                                    y=scatters.list_text_y,
                                                    text_list=scatters.list_text_s,
                                                    textsize=fontsize,
                                                    x_lines=plots_x_to_avoid,
                                                    y_lines=plots_y_to_avoid,
                                                    x_scatter=scatters.scatters_to_avoid_x,
                                                    y_scatter=scatters.scatters_to_avoid_y,
                                                    scatter_sizes=scatters.scatter_to_avoid_sizes,
                                                    max_distance=max_distance,
                                                    min_distance=min_distance,
                                                    margin=margin,
                                                    nbr_candidates=nbr_candidates,
                                                    linewidth=output_linewidth,
                                                    draw_lines=True,
                                                    draw_all=False,
                                                    priority_strategy="largest",
                                                    avoid_label_lines_overlap=True,
                                                    avoid_crossing_label_lines=True,
                                                    ha=ha,
                                                    va=va,
                                                    fontproperties=fontproperties)

    list_text_data: list[TextData] = []
    list_plot_data: list[PlotData] = []
    for i, (text, line) in enumerate(zip(result_text_xy, result_line)):
        assert text is not None, "Failed to allocate text, consider using larger margins in VerticalLayout " \
            "or larger `max_distance` when calling `allocate_text`"
        assert_len(text, 3)
        text_x, text_y, _ = text
        list_text_data.append(TextData(x=text_x, y=text_y, s=scatters.list_text_s[i],
                                       fontsize=fontsize, fontproperties=fontproperties, ha=ha, va=va))

        assert line is not None
        assert_len(line, 3)
        line_x, line_y, _ = line
        list_plot_data.append(PlotData(x=list(line_x), y=list(line_y), linewidth=output_linewidth))

    logger.info("Succesful Text Allocation")

    if DEBUG_TEXT_ALLOCATION:
        debug_fig, debug_ax = plt.subplots()
        base_fig.setup(debug_fig, debug_ax)
        debug_fig.set_dpi(600 / debug_fig.get_size_inches()[0])

        for list_x, list_y in zip(plots_x_to_avoid, plots_y_to_avoid):
            plt.plot(list_x, list_y, "-r")

        for data in list_text_data + list_plot_data:
            data.plot(debug_ax, "g")

        plt.savefig(os.path.join(DATA_DIR, "text_after.svg"))
        plt.show()

    return list_text_data, list_plot_data


@dataclass
class AnnotatedScatterDataCollection:
    """List of scatter points with optional text annotations.

    Following fields are used to allocate text annotations:
    - list_text_x: list of x-coordinates that text annotations are tied to
    - list_text_y: list of y-coordinates that text annotations are tied to
    - list_text_s: list of text annotation strings

    The field `list_text_markersize` stores the size of the marker that the text annotation is tied to.

    Whereas the field `list_scatter_data` stored all scatter points, which are used as obstacles to avoid text overlap.
    """
    list_text_x: list[float] = field(default_factory=list)
    list_text_y: list[float] = field(default_factory=list)
    list_text_s: list[str] = field(default_factory=list)
    list_text_markersize: list[float] = field(default_factory=list)

    list_scatter_data: list[ScatterData] = field(default_factory=list)

    def add_scatter_data(self,
                         global_x: list[float],
                         global_y: list[float],
                         scatter_ids: list[int],
                         scatter_texts: list[str] | list[str | None],
                         marker: str | Path,
                         markersize: float) -> None:
        """Add scatter data."""
        assert_same_len((global_x, global_y))
        assert_same_len((scatter_ids, scatter_texts))
        scatter_data = ScatterData(x=[global_x[idx] for idx in scatter_ids],
                                   y=[global_y[idx] for idx in scatter_ids],
                                   marker=marker, markersize=markersize)
        self.list_scatter_data.append(scatter_data)

        for x, y, s in zip(scatter_data.x, scatter_data.y, scatter_texts):
            if s is not None:
                self.list_text_x.append(x)
                self.list_text_y.append(y)
                self.list_text_s.append(s)
                self.list_text_markersize.append(markersize)

    @property
    def scatters_to_avoid_x(self) -> list[float]:
        """Scatters to avoid x."""
        return [x
                for scatter_data in self.list_scatter_data
                for x in scatter_data.x]

    @property
    def scatters_to_avoid_y(self) -> list[float]:
        """Scatters to avoid y."""
        return [y
                for scatter_data in self.list_scatter_data
                for y in scatter_data.y]

    @property
    def scatter_to_avoid_sizes(self) -> list[float]:
        """Scatter to avoid sizes."""
        return [s
                for scatter_data in self.list_scatter_data
                for s in [scatter_data.markersize]*len(scatter_data.x)]
