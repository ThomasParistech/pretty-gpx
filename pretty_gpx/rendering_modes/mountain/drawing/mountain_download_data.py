#!/usr/bin/python3
"""Mountain Download Data."""
from dataclasses import dataclass

import numpy as np

from pretty_gpx.common.drawing.base_drawing_figure import BaseDrawingFigure
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.structure import AugmentedGpxData
from pretty_gpx.common.structure import DownloadData
from pretty_gpx.rendering_modes.mountain.data.elevation_map import download_elevation_map
from pretty_gpx.rendering_modes.mountain.mountain_vertical_layout import MountainVerticalLayout


@dataclass
class MountainDownloadData(DownloadData):
    """MountainDownloadData."""
    img_bounds: GpxBounds
    layout: MountainVerticalLayout
    paper_fig: BaseDrawingFigure
    elevation: np.ndarray

    @staticmethod
    def from_gpx_and_paper_size(gpx_data: AugmentedGpxData, paper: PaperSize) -> 'MountainDownloadData':
        """Init the DownloadData from GPX data and Paper Size."""
        layout = MountainVerticalLayout.default()
        img_bounds, paper_fig = layout.get_download_bounds_and_paper_figure(gpx_data.track, paper)
        elevation = download_elevation_map(img_bounds)
        return MountainDownloadData(bounds=img_bounds,
                                    layout=layout,
                                    img_bounds=img_bounds,
                                    paper_fig=paper_fig,
                                    elevation=elevation)
