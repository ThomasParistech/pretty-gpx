#!/usr/bin/python3
"""Fonts."""
import os
from enum import Enum

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
