#!/usr/bin/python3
"""Ui Fonts Menu, to select a font from a list."""
import os
from collections.abc import Awaitable
from collections.abc import Callable
from dataclasses import dataclass
from typing import Self

from matplotlib.font_manager import FontProperties
from nicegui import app
from nicegui import ui

from pretty_gpx.common.drawing.utils.fonts import get_css_header
from pretty_gpx.common.utils.paths import FONTS_DIR
from pretty_gpx.common.utils.utils import safe


@dataclass
class UiFontsMenu:
    """NiceGui menu to select a font in a list."""

    button: ui.dropdown_button
    fonts: tuple[FontProperties, ...]

    @classmethod
    def create(cls,
               *,
               label: str,
               fonts_l: tuple[FontProperties, ...],
               tooltip: str,
               on_change: Callable[[], Awaitable[None]]) -> Self:
        """Create a UiFontsMenu."""
        default_font = fonts_l[0].get_name()
        ui.label(label)
        with ui.dropdown_button(default_font, auto_close=True) as button:
            button.tooltip(tooltip)
            button.classes('bg-white text-black w-48 justify-start')
            button.style(f'display: block; font-family: "{default_font}"; width: 100%;'
                         'border: 1px solid #ddd; border-radius: 4px; position: relative;')
            for font in fonts_l:
                font_css_header = get_css_header(font=font)
                if font_css_header is not None:
                    ui.add_css(font_css_header)
                font_name = font.get_name()

                def create_click_handler(selected_font: str) -> Callable[[], Awaitable[None]]:
                    async def handler() -> None:
                        button.text = selected_font
                        button.style(f'font-family: "{selected_font}";')
                        await on_change()
                    return handler
                ui.item(font_name, on_click=create_click_handler(font_name)) \
                    .style(f'display: block; font-family:"{font_name}"; width: 100%;'
                           'border: 1px solid #ddd; border-radius: 4px; position: relative;')
        return cls(button, fonts_l)


@dataclass
class UiFontsMenuFontProp(UiFontsMenu):
    """NiceGUI Str Dropdown Wrapper."""

    @property
    def value(self) -> FontProperties:
        """Return the value."""
        str_to_font = {font.get_name(): font for font in self.fonts}
        font_output = str_to_font.get(self.button.text, None)
        if font_output is None:
            raise KeyError
        else:
            return font_output
