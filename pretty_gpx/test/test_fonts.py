#!/usr/bin/python3
"""Test Fonts."""

from collections.abc import Iterable
from io import BytesIO
from warnings import catch_warnings

import matplotlib
import matplotlib.pyplot as plt
import pytest
from matplotlib.font_manager import findfont

from pretty_gpx.common.drawing.utils.fonts import CustomFont
from pretty_gpx.common.drawing.utils.fonts import STATS_FONTS
from pretty_gpx.common.utils.asserts import assert_isfile


def test_fonts_available() -> None:
    """Test that all fonts are available."""
    for font in CustomFont:
        font_path = findfont(font.value)
        assert_isfile(font_path, msg=f"Font {font.value.get_name()} not found at {font_path}")


def test_fonts_matplotlib() -> None:
    """Test that matplotlib can use the fonts."""
    matplotlib.use('Agg')
    plt.figure()
    for font in CustomFont:
        plt.text(0.5, 0.5, "This is a Test", fontproperties=font.value)
        plt.gcf()
    plt.close()


def __assert_available_glyphs(fonts: Iterable[CustomFont], string_to_test: str) -> None:
    """Assert that all glyphs present in the input `string_to_test` are available in the fonts."""
    matplotlib.use('Agg')
    plt.figure()
    with catch_warnings(record=True) as wlist:
        for font in fonts:
            plt.text(0.5, 0.5, string_to_test, fontproperties=font.value)
            plt.savefig(BytesIO(), format='png')
    plt.close()
    assert len(wlist) == 0, "\n".join([str(w) for w in wlist])


def test_stats_fonts_matplotlib_numbers() -> None:
    """Test that matplotlib can use the stats fonts with numbers."""
    with pytest.raises(AssertionError):
        __assert_available_glyphs(fonts=list(CustomFont), string_to_test="1234567890 +-")

    __assert_available_glyphs(fonts=STATS_FONTS, string_to_test="123456789")
    __assert_available_glyphs(fonts=STATS_FONTS, string_to_test="+-")
