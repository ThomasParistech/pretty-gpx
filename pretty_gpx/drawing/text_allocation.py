#!/usr/bin/python3
"""Text Allocation."""
import os

import matplotlib.pyplot as plt
import numpy as np
import textalloc as ta
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties

from pretty_gpx import DATA_DIR
from pretty_gpx.drawing.drawing_data import PlotData
from pretty_gpx.drawing.drawing_data import TextData
from pretty_gpx.drawing.drawing_figure import BaseDrawingFigure

DEBUG_TEXT_ALLOCATION = False


def allocate_text(fig: Figure,
                  ax: Axes,
                  imshow_img: np.ndarray,
                  w_mm: float,
                  latlon_aspect_ratio: float,
                  x: list[float],
                  y: list[float],
                  s: list[str],
                  plots_x_to_avoid: list[list[float]],
                  plots_y_to_avoid: list[list[float]],
                  fontsize: float,
                  fontproperties: FontProperties,
                  output_linewidth: float,
                  min_distance: float = 0.04,
                  max_distance: float = 0.2,
                  margin: float = 0.008,
                  nbr_candidates: int = 300,
                  ha: str = 'center') -> tuple[list[TextData], list[PlotData]]:
    """Allocate text-boxes in imshow plot while avoiding overlap with other annotations."""
    base_fig = BaseDrawingFigure(w_mm=w_mm, latlon_aspect_ratio=latlon_aspect_ratio)
    base_fig.imshow(fig, ax, imshow_img)

    print(f"Optimize {len(s)} Text Allocations...")

    if DEBUG_TEXT_ALLOCATION:
        debug_fig, debug_ax = plt.subplots()
        base_fig.imshow(debug_fig, debug_ax, imshow_img)
        base_fig.adjust_display_width(debug_fig, 600)
        for list_x, list_y in zip(plots_x_to_avoid, plots_y_to_avoid):
            debug_ax.plot(list_x, list_y, "-r")
        for text_x, text_y, text_s in zip(x, y, s):
            debug_ax.text(text_x, text_y, text_s, ha="center", va="center",
                          fontsize=fontsize, fontproperties=fontproperties)
        plt.title("Texts to Allocate")
        plt.savefig(os.path.join(DATA_DIR, "text_before.svg"))
        plt.show()

    result_text_xy, result_line = ta.allocate(ax,
                                              x=x,
                                              y=y,
                                              text_list=s,
                                              textsize=fontsize,
                                              x_lines=plots_x_to_avoid,
                                              y_lines=plots_y_to_avoid,
                                              max_distance=max_distance,
                                              min_distance=min_distance,
                                              margin=margin,
                                              nbr_candidates=nbr_candidates,
                                              linewidth=output_linewidth,
                                              draw_lines=True,
                                              draw_all=False,
                                              avoid_label_lines_overlap=True,
                                              ha=ha,
                                              fontproperties=fontproperties)

    list_text_data: list[TextData] = []
    list_plot_data: list[PlotData] = []
    for i, (text, line) in enumerate(zip(result_text_xy, result_line)):
        assert text is not None, "Failed to allocate text, consider using larger margins in VerticalLayout " \
            "or larger `max_distance` when calling `allocate_text`"
        text_x, text_y = text
        list_text_data.append(TextData(x=text_x, y=text_y, s=s[i],
                                       fontsize=fontsize, fontproperties=fontproperties, ha=ha))

        assert line is not None
        line_x, line_y = line
        list_plot_data.append(PlotData(x=list(line_x), y=list(line_y), linewidth=output_linewidth))

    print("Succesful Text Allocation")

    if DEBUG_TEXT_ALLOCATION:
        base_fig.imshow(fig, ax, imshow_img)
        base_fig.adjust_display_width(fig, 600)

        for list_x, list_y in zip(plots_x_to_avoid, plots_y_to_avoid):
            plt.plot(list_x, list_y, "-r")

        for data in list_text_data + list_plot_data:
            data.plot(ax, "g", imshow_img.shape, imshow_img.shape)
        plt.savefig(os.path.join(DATA_DIR, "text_after.svg"))
        plt.show()

    return list_text_data, list_plot_data
