#!/usr/bin/python3
"""Test Mountain Drawer."""

import matplotlib.pyplot as plt

from pretty_gpx.common.data.examples import HikingGpx
from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.rendering_modes.mountain.drawing.mountain_drawer import MountainDrawer
from pretty_gpx.rendering_modes.mountain.drawing.mountain_params import MountainParams


def __core_test_mountain_drawer(scene: HikingGpx) -> None:
    """Test Mountain Drawer."""
    drawer = MountainDrawer(params=MountainParams.default(), top_ratio=0.18, bot_ratio=0.22, margin_ratio=0.1)
    drawer.change_gpx(scene.path, PAPER_SIZES["A4"])
    for paper_size in [PAPER_SIZES["32x32"], PAPER_SIZES["A4"], PAPER_SIZES["40x30"]]:
        drawer.change_papersize(paper_size)
        fig, ax = plt.subplots()
        drawer.draw(fig, ax, high_resolution=False)


def test_cabaliros_mountain_drawer() -> None:
    """Test Cabaliros Mountain Drawer."""
    __core_test_mountain_drawer(HikingGpx.CABALIROS)
