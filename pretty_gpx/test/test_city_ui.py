#!/usr/bin/python3
"""Test City UI."""

import os

from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.utils.paths import RUNNING_DIR
from pretty_gpx.ui.pages.city.page import CityUiCache


def __core_test_city_ui(path: str) -> None:
    """Test City UI."""
    gpx_data, _ = CityUiCache.get_gpx_data(path)
    paper = PAPER_SIZES["A4"]
    download_data, _ = CityUiCache.get_download_data(gpx_data, paper)
    cache, _ = CityUiCache.from_gpx_and_download_data(gpx_data, download_data)
    assert cache.is_initialized()


def test_4_chateaux_city_ui_() -> None:
    """Test Route des 4 Chateaux City UI."""
    __core_test_city_ui(os.path.join(RUNNING_DIR, "route_4_chateaux.gpx"))
