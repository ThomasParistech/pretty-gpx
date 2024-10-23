#!/usr/bin/python3
"""List Rendering Modes to display in the GUI."""
from typing import Final

from pretty_gpx.rendering_modes.city.ui.page import city_page
from pretty_gpx.rendering_modes.mountain.ui.page import mountain_page
from pretty_gpx.rendering_modes.rendering_mode import RenderingMode

RENDERING_MODES: Final[list[RenderingMode]] = [
    RenderingMode.from_page(mountain_page),
    RenderingMode.from_page(city_page),
]
