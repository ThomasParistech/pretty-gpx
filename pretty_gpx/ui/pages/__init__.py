#!/usr/bin/python3
"""List Rendering Modes to display in the GUI."""
from typing import Final

from pretty_gpx.ui.pages.city.page import city_page
from pretty_gpx.ui.pages.mountain.page import mountain_page
from pretty_gpx.ui.pages.page.rendering_page import RenderingPage

RENDERING_PAGES: Final[list[RenderingPage]] = [
    RenderingPage.from_page(mountain_page),
    RenderingPage.from_page(city_page),
]
