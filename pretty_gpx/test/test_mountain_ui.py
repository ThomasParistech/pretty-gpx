#!/usr/bin/python3
"""Test Mountain UI."""

import os

from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.utils.paths import HIKING_DIR
from pretty_gpx.ui.pages.mountain.page import MountainUiCache


def __core_test_mountain_ui(path: str) -> None:
    """Test Mountain UI."""
    gpx_data, _ = MountainUiCache.get_gpx_data([path])
    paper = PAPER_SIZES["A4"]
    download_data, _ = MountainUiCache.get_download_data(gpx_data, paper)
    cache, _ = MountainUiCache.from_gpx_and_download_data(gpx_data, download_data)
    assert cache.is_initialized()


def test_cabaliros_mountain_ui_() -> None:
    """Test Cabaliros Mountain UI."""
    __core_test_mountain_ui(os.path.join(HIKING_DIR, "cabaliros.gpx"))
