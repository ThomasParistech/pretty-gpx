#!/usr/bin/python3
"""Mountain Drawing Style/Size Config."""
from dataclasses import dataclass

from matplotlib.path import Path

from pretty_gpx.common.drawing.plt_marker import MarkerType
from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.utils import mm_to_point


@dataclass(kw_only=True)
class MountainDrawingStyleConfig:
    """Mountain Drawing Style Config."""
    start_marker: Path = MarkerType.DISK.path()
    end_marker: Path = MarkerType.SQUARE.path()
    peak_marker: Path = MarkerType.TRIANGLE.path()
    hut_marker: Path = MarkerType.HOUSE.path()


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
        ref_diag_mm = PAPER_SIZES["A4"].diag_mm
        new_diag_mm = paper_size.diag_mm
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
