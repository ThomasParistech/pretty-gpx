#!/usr/bin/python3
"""Test City Drawer."""

import matplotlib.pyplot as plt

from pretty_gpx.common.data.examples import RunningGpx
from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.rendering_modes.city.drawing.city_drawer import CityDrawer
from pretty_gpx.rendering_modes.city.drawing.city_params import CityParams


def __core_test_city_drawer(scene: RunningGpx) -> None:
    """Test City Drawer."""
    drawer = CityDrawer(params=CityParams.default(), top_ratio=0.18, bot_ratio=0.22, margin_ratio=0.1)
    drawer.change_gpx(scene.path, PAPER_SIZES["A4"])
    for paper_size in [PAPER_SIZES["32x32"], PAPER_SIZES["A4"], PAPER_SIZES["40x30"]]:
        drawer.change_papersize(paper_size)
        fig, ax = plt.subplots()
        drawer.draw(fig, ax, high_resolution=False)


def test_10k_paris_city_drawer() -> None:
    """Test 10k Paris City Drawer."""
    __core_test_city_drawer(RunningGpx.TEN_K_PARIS)
