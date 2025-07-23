#!/usr/bin/python3
"""Ui Fonts Menu, to select a font from a list."""
import os
from collections.abc import Awaitable
from collections.abc import Callable
from dataclasses import dataclass
from typing import Self

from nicegui import app
from nicegui import ui

from pretty_gpx.common.drawing.utils.fonts import CustomFont
from pretty_gpx.common.utils.paths import FONTS_DIR

app.add_static_files('/fonts', os.path.abspath(FONTS_DIR))


@dataclass
class UiFontsMenu:
    """NiceGui menu to select a font in a list."""

    button: ui.dropdown_button
    fonts: tuple[CustomFont, ...]

    @classmethod
    def create(cls,
               *,
               fonts: tuple[CustomFont, ...],
               tooltip: str,
               on_change: Callable[[], Awaitable[None]],
               start_font: CustomFont | None = None) -> Self:
        """Create a UiFontsMenu."""
        if start_font is None:
            start_font = fonts[0]

        with ui.dropdown_button(start_font.font_name, auto_close=True) as button:
            button.tooltip(tooltip)
            button.classes('bg-white text-black w-48 justify-start')
            button.style(f'display: block; font-family: "{start_font.font_name}"; width: 100%;'
                         'border: 1px solid #ddd; border-radius: 4px; position: relative;')

            for font in fonts:
                font_css_header = font.get_css_header()
                if font_css_header is not None:
                    ui.add_css(font_css_header)

                def create_click_handler(selected_font: str) -> Callable[[], Awaitable[None]]:
                    async def handler() -> None:
                        button.text = selected_font
                        button.style(f'font-family: "{selected_font}";')
                        await on_change()
                    return handler

                ui.item(font.font_name, on_click=create_click_handler(font.font_name)) \
                    .style(f'display: block; font-family:"{font.font_name}"; width: 100%;'
                           'border: 1px solid #ddd; border-radius: 4px; position: relative;')

        return cls(button, fonts)

    @property
    def value(self) -> CustomFont:
        """Return the selected font."""
        for f in self.fonts:
            if f.font_name == self.button.text:
                return f
        raise ValueError(f"Selected font '{self.button.text}' not found in available fonts.")
