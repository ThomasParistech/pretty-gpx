#!/usr/bin/python3
"""Mountain Drawing Style/Size Config."""
import os
from dataclasses import dataclass

import numpy as np
from matplotlib.path import Path

from pretty_gpx.common.drawing.plt_marker import marker_from_svg
from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.paths import ICONS_DIR
from pretty_gpx.common.utils.utils import mm_to_point


@dataclass(kw_only=True)
class MountainDrawingStyleConfig:
    """Mountain Drawing Style Config."""
    start_marker: str | Path = "o"
    end_marker: str | Path = "s"
    peak_marker: str | Path = "^"
    hut_marker: str | Path = marker_from_svg(os.path.join(ICONS_DIR, "house.svg"))


@dataclass(kw_only=True)
class MountainDrawingSizeConfig:
    """Mountain Drawing Size Config."""
    text_fontsize: float
    text_arrow_linewidth: float
    title_fontsize: float
    stats_fontsize: float

    start_markersize: float
    end_markersize: float
    peak_markersize: float
    hut_markersize: float

    track_linewidth: float

    ref_paper_size: PaperSize

    @staticmethod
    def default(paper_size: PaperSize) -> 'MountainDrawingSizeConfig':
        """Default Mountain Drawing Size Config."""
        # Convert default A4 parameters to paper size
        ref_diag_mm = np.linalg.norm([PAPER_SIZES["A4"].w_mm, PAPER_SIZES["A4"].h_mm])
        new_diag_mm = np.linalg.norm([paper_size.w_mm, paper_size.h_mm])
        scale = float(new_diag_mm/ref_diag_mm)
        return MountainDrawingSizeConfig(text_fontsize=mm_to_point(3.0) * scale,
                                         text_arrow_linewidth=mm_to_point(0.3) * scale,
                                         title_fontsize=mm_to_point(20.0) * scale,
                                         stats_fontsize=mm_to_point(14) * scale,
                                         start_markersize=mm_to_point(3.5) * scale,
                                         end_markersize=mm_to_point(3.5) * scale,
                                         peak_markersize=mm_to_point(3.5) * scale,
                                         hut_markersize=mm_to_point(7.0) * scale,
                                         track_linewidth=mm_to_point(1.0) * scale,
                                         ref_paper_size=paper_size)
