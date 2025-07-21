#!/usr/bin/python3
"""Fonts."""
import os
import textwrap
from enum import Enum
from pathlib import Path

from matplotlib.font_manager import FontProperties

from pretty_gpx.common.utils.paths import FONTS_DIR


class CustomFont(Enum):
    """Custom Fonts Enum."""
    DEJA_VU_SANS_BOLD = FontProperties(family="DejaVu Sans", weight="bold")
    LOBSTER = FontProperties(family="Lobster", fname=os.path.join(FONTS_DIR, "Lobster.ttf"))
    MONOTON = FontProperties(family="Monoton", fname=os.path.join(FONTS_DIR, "Monoton.ttf"))
    GOCHI_HAND = FontProperties(family="Gochi Hand", fname=os.path.join(FONTS_DIR, "GochiHand.ttf"))
    EMILIO_20 = FontProperties(family="Emilio 20", fname=os.path.join(FONTS_DIR, "Emilio20.ttf"))
    ALLERTA_STENCIL = FontProperties(family="Allerta Stencil", fname=os.path.join(FONTS_DIR, "AllertaStencil.ttf"))

    @property
    def font_name(self) -> str:
        """Get the font name."""
        return self.value.get_name()

    def get_css_header(self) -> str | None:
        """Get the CSS header for the font."""
        font_path = self.value.get_file()
        if font_path is None or not isinstance(font_path, str):
            return None

        font_path = Path(font_path).name
        if font_path.lower().endswith('.otf'):
            font_format = 'opentype'
        elif font_path.lower().endswith('.ttf'):
            font_format = 'truetype'
        else:
            raise ValueError("Unsupported font format. Please provide a .otf or .ttf file.")

        header = f'''
            @font-face {{
                font-family: '{self.font_name}';
                src: url('/fonts/{font_path}') format('{font_format}');
            }}
        '''
        return textwrap.dedent(header)
