#!/usr/bin/python3
"""Mountain Drawing Cache Data."""
from dataclasses import dataclass

from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.rendering_modes.mountain.data.augmented_gpx_data import AugmentedGpxData
from pretty_gpx.rendering_modes.mountain.drawing.mountain_drawer import MountainDrawer
from pretty_gpx.ui.pages.template.ui_plot import HIGH_RES_DPI
from pretty_gpx.ui.pages.template.ui_plot import WORKING_DPI


@dataclass
class MountainDrawingCacheData:
    """Mountain Drawing Cache Data."""
    low_res: MountainDrawer
    high_res: MountainDrawer

    gpx_data: AugmentedGpxData

    def __post_init__(self) -> None:
        assert self.low_res.dpi < self.high_res.dpi

    @staticmethod
    def from_gpx(list_gpx_path: str | bytes | list[str] | list[bytes],
                 paper_size: PaperSize) -> 'MountainDrawingCacheData':
        """Create a MountainPosterImageCaches from a GPX file."""
        # Extract GPX data and retrieve close mountain passes/huts
        gpx_data = AugmentedGpxData.from_path(list_gpx_path)
        return MountainDrawingCacheData.from_augmented_gpx_data(gpx_data, paper_size)

    @staticmethod
    def from_augmented_gpx_data(gpx_data: AugmentedGpxData,
                                paper_size: PaperSize) -> 'MountainDrawingCacheData':
        """Create a MountainPosterImageCaches from a GPX file."""
        high_res = MountainDrawer.from_gpx_data(gpx_data, dpi=HIGH_RES_DPI, paper=paper_size)
        low_res = high_res.change_dpi(WORKING_DPI)
        return MountainDrawingCacheData(low_res=low_res, high_res=high_res, gpx_data=gpx_data)
