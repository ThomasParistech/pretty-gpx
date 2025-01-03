#!/usr/bin/python3
"""Rendering Page."""
import inspect
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

from pretty_gpx.common.utils.asserts import assert_eq
from pretty_gpx.common.utils.asserts import assert_same_keys
from pretty_gpx.common.utils.paths import MAIN_DIR
from pretty_gpx.common.utils.utils import snake_case_to_label

PAGE_PY: Final[str] = "page.py"
EXAMPLE_SVG: Final[str] = "example.svg"
ICON_SVG: Final[str] = "icon.svg"


@dataclass
class RenderingPage:
    """Rendering Page."""
    name: str
    ui_page: Callable[[], None]
    example_svg: str
    icon_svg: str

    @staticmethod
    def from_page(mode_page: Callable[[], None]) -> 'RenderingPage':
        """Init RenderingMode from page function of a given mode.

        Each mode must follow this directory structure:

            pretty_gpx/ui/rendering_pages/<mode>/
                                            ├── __init__.py
                                            ├── page.py
                                            ├── example.svg
                                            ├── icon.svg

        Args:
            mode_page: NiceGUI Page Function of the given mode

        Returns:
            RenderingPage
        """
        assert mode_page.__name__.endswith("_page"), f"Function must be named '<mode>_page'. Got {mode_page.__name__}"
        mode = mode_page.__name__[:-len("_page")]

        mode_dir = os.path.join(MAIN_DIR, "pretty_gpx", "ui", "pages", mode)
        assert_eq(os.path.abspath(inspect.getfile(mode_page)), os.path.join(mode_dir, PAGE_PY),
                  msg=f"Page function of '{mode}' mode must be in the 'ui' subdirectory")

        mode_files = [f.name for f in os.scandir(mode_dir) if f.is_file() and not f.name.startswith(".")]
        assert_same_keys(mode_files, {PAGE_PY, EXAMPLE_SVG, ICON_SVG, "__init__.py"},
                         msg=f"Missing files for '{mode}' mode")

        return RenderingPage(name=snake_case_to_label(mode),
                             ui_page=mode_page,
                             example_svg=os.path.join(mode_dir, EXAMPLE_SVG),
                             icon_svg=os.path.join(mode_dir, ICON_SVG))

    @property
    def page_path(self) -> str:
        """Get Page Path of a given rendering mode."""
        return f'/{self.name.lower()}/'
