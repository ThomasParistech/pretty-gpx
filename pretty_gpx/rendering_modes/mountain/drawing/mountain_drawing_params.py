#!/usr/bin/python3
"""Mountain Drawing Parameters."""
import os
from dataclasses import dataclass

import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path

from pretty_gpx.common.drawing.plt_marker import marker_from_svg
from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.paths import FONTS_DIR
from pretty_gpx.common.utils.paths import ICONS_DIR
from pretty_gpx.common.utils.utils import mm_to_point


@dataclass(kw_only=True)
class MountainDrawingStyleParams:
    """Drawing Style Parameters."""
    start_marker: str | Path = "o"
    end_marker: str | Path = "s"
    peak_marker: str | Path = "^"
    hut_marker: str | Path = marker_from_svg(os.path.join(ICONS_DIR, "house.svg"))

    classic_font: FontProperties = FontProperties(weight="bold")
    pretty_font: FontProperties = FontProperties(fname=os.path.join(FONTS_DIR, "Lobster 1.4.otf"))


@dataclass(kw_only=True)
class MountainDrawingSizeParams:
    """Drawing Size Parameters."""
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

    def change_paper_size(self, new_paper_size: PaperSize) -> "MountainDrawingSizeParams":
        """Scale parameters to new paper size."""
        current_diag_mm = np.linalg.norm([self.ref_paper_size.w_mm, self.ref_paper_size.h_mm])
        new_diag_mm = np.linalg.norm([new_paper_size.w_mm, new_paper_size.h_mm])
        scale = float(new_diag_mm/current_diag_mm)

        return MountainDrawingSizeParams(text_fontsize=self.text_fontsize*scale,
                                         text_arrow_linewidth=self.text_arrow_linewidth*scale,
                                         title_fontsize=self.title_fontsize*scale,
                                         stats_fontsize=self.stats_fontsize*scale,
                                         start_markersize=self.start_markersize*scale,
                                         end_markersize=self.end_markersize*scale,
                                         peak_markersize=self.peak_markersize*scale,
                                         hut_markersize=self.hut_markersize*scale,
                                         track_linewidth=self.track_linewidth*scale,
                                         ref_paper_size=new_paper_size)

    @staticmethod
    def default(paper_size: PaperSize) -> 'MountainDrawingSizeParams':
        """Default Drawing Size Parameters."""
        # Convert default A4 parameters to paper size
        ref_diag_mm = np.linalg.norm([PAPER_SIZES["A4"].w_mm, PAPER_SIZES["A4"].h_mm])
        new_diag_mm = np.linalg.norm([paper_size.w_mm, paper_size.h_mm])
        scale = float(new_diag_mm/ref_diag_mm)
        return MountainDrawingSizeParams(text_fontsize=mm_to_point(3.0) * scale,
                                         text_arrow_linewidth=mm_to_point(0.3) * scale,
                                         title_fontsize=mm_to_point(20.0) * scale,
                                         stats_fontsize=mm_to_point(18.5) * scale,
                                         start_markersize=mm_to_point(3.5) * scale,
                                         end_markersize=mm_to_point(3.5) * scale,
                                         peak_markersize=mm_to_point(3.5) * scale,
                                         hut_markersize=mm_to_point(7.0) * scale,
                                         track_linewidth=mm_to_point(1.0) * scale,
                                         ref_paper_size=paper_size)
