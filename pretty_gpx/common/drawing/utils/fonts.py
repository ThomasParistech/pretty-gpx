#!/usr/bin/python3
"""Fonts."""
import os
import textwrap
from enum import Enum
from pathlib import Path

from matplotlib.font_manager import FontProperties

from pretty_gpx.common.utils.paths import FONTS_DIR


def get_css_header(font: FontProperties) -> str | None:
    """Get the CSS header when using a custom font (using a local file)."""
    font_path = font.get_file()
    if font_path is not None and isinstance(font_path, str):
        font_path = Path(font_path).name
        header = f'''
            @font-face {{
                font-family: '{font.get_name()}';
                src: url('/fonts/{font_path}') format('opentype');
            }}
        '''
        return textwrap.dedent(header)
    else:
        return None


class FontEnum(Enum):
    """Font Enum."""
    ANNOTATION = FontProperties(weight="bold")
    TITLE = (FontProperties(family="Lobster 1.4.otf", fname=os.path.join(FONTS_DIR, "Lobster 1.4.otf")),
             FontProperties(family="Arial"),
             FontProperties(family="Verdana"),
             FontProperties(family="Times New Roman"),
             FontProperties(family="Georgia"),
             FontProperties(family="Comic Sans MS"))
    STATS = FontProperties(family="Lobster 1.4.otf", fname=os.path.join(FONTS_DIR, "Lobster 1.4.otf"))

