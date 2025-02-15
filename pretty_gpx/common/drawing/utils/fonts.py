#!/usr/bin/python3
"""Fonts."""
import os
import textwrap
from enum import Enum
from pathlib import Path

from matplotlib.font_manager import FontProperties

from pretty_gpx.common.utils.paths import FONTS_DIR


def get_font_format(font_path: str) -> str:
    """Get font's type."""
    if font_path.lower().endswith('.otf'):
        return 'opentype'
    elif font_path.lower().endswith('.ttf'):
        return 'truetype'
    else:
        raise ValueError("Unsupported font format. Please provide a .otf or .ttf file.")


def get_css_header(font: FontProperties) -> str | None:
    """Get the CSS header when using a custom font (using a local file)."""
    font_path = font.get_file()
    if font_path is not None and isinstance(font_path, str):
        font_path = Path(font_path).name
        header = f'''
            @font-face {{
                font-family: '{font.get_name()}';
                src: url('/fonts/{font_path}') format('{get_font_format(font_path)}');
            }}
        '''
        return textwrap.dedent(header)
    else:
        return None


class FontEnum(Enum):
    """Font Enum."""
    ANNOTATION = FontProperties(weight="bold")
    TITLE = (FontProperties(family="Lobster", fname=os.path.join(FONTS_DIR, "Lobster.ttf")),
             FontProperties(family="Verdana"),
             FontProperties(family="Comic Sans MS"),
             FontProperties(family="Monoton", fname=os.path.join(FONTS_DIR, "Monoton.ttf")),
             FontProperties(family="GochiHand", fname=os.path.join(FONTS_DIR, "GochiHand.ttf")),
             FontProperties(family="Emilio20", fname=os.path.join(FONTS_DIR, "Emilio20.ttf")),
             FontProperties(family="AllertaStencil", fname=os.path.join(FONTS_DIR, "AllertaStencil.ttf"))
    )
    STATS = FontProperties(family="Lobster", fname=os.path.join(FONTS_DIR, "Lobster.ttf"))

