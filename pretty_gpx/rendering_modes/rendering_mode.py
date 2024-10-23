#!/usr/bin/python3
"""Rendering Mode."""
import inspect
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

from pretty_gpx.common.utils.asserts import assert_eq
from pretty_gpx.common.utils.asserts import assert_same_keys
from pretty_gpx.common.utils.paths import MAIN_DIR

PAGE_PY: Final[str] = "page.py"
EXAMPLE_SVG: Final[str] = "example.svg"
ICON_SVG: Final[str] = "icon.svg"


@dataclass
class RenderingMode:
    """Rendering Mode."""
    name: str
    ui_page: Callable[[], None]
    example_svg: str
    icon_svg: str

    @staticmethod
    def from_page(mode_page: Callable[[], None]) -> 'RenderingMode':
        """Init RenderingMode from page function of a given mode.

        Each mode must follow this directory structure:

            pretty_gpx/rendering_modes/<mode>/ui/
                                               ├── __init__.py
                                               ├── page.py
                                               ├── example.svg
                                               ├── icon.svg

        Args:
            mode_page: NiceGUI Page Function of the given mode

        Returns:
            RenderingMode
        """
        assert mode_page.__name__.endswith("_page"), f"Page function must be '<mode>_page'. Got {mode_page.__name__}"
        mode = mode_page.__name__[:-len("_page")]
        assert "_" not in mode, "Mode name must not contain underscores"

        ui_subdir = os.path.join(MAIN_DIR, "pretty_gpx", "rendering_modes", mode, "ui")
        assert_eq(os.path.abspath(inspect.getfile(mode_page)), os.path.join(ui_subdir, PAGE_PY),
                  msg=f"Page function of '{mode}' mode must be in the 'ui' subdirectory")

        ui_files = [f.name for f in os.scandir(ui_subdir) if f.is_file() and not f.name.startswith(".")]
        assert_same_keys(ui_files, {PAGE_PY, EXAMPLE_SVG, ICON_SVG, "__init__.py"},
                         msg=f"Missing files for '{mode}' mode")

        return RenderingMode(name=mode.capitalize(),
                             ui_page=mode_page,
                             example_svg=os.path.join(ui_subdir, EXAMPLE_SVG),
                             icon_svg=os.path.join(ui_subdir, ICON_SVG))
