#!/usr/bin/python3
"""Ui Fonts Menu, to select a font from a list."""
import os
import textwrap
from collections.abc import Awaitable
from collections.abc import Callable

from nicegui import app
from nicegui import ui

from pretty_gpx.common.drawing.utils.fonts import CustomFont
from pretty_gpx.common.utils.paths import FONTS_DIR

app.add_static_files('/fonts', os.path.abspath(FONTS_DIR))


class UiFontSelect:
    """NiceGui menu to select a font in a list."""

    def __init__(self,
                 *,
                 label: str,
                 fonts: tuple[CustomFont, ...],
                 on_change: Callable[[], Awaitable[None]],
                 start_font: CustomFont | None = None) -> None:
        """Create a UiFontsMenu."""
        if start_font is None:
            current_idx = 0
        else:
            current_idx = fonts.index(start_font)  # Can raise ValueError if not found

        def on_click_idx(idx: int) -> Callable[[], Awaitable[None]]:
            """On click handler."""
            async def handler() -> None:
                self.change_current_idx(idx)
                await on_change()
            return handler

        with ui.dropdown_button(label, icon="font_download", auto_close=True) as main_button:
            main_button.classes("bg-white text-black normal-case")

            for font in fonts:
                font_css_header = get_css_header(font)
                if font_css_header is not None:
                    ui.add_css(font_css_header)

            items = [ui.item(font.name.title().replace("_", " "), on_click=on_click_idx(idx))
                     .style(f'font-family:"{font.font_name}";')
                     for idx, font in enumerate(fonts)]

        ###

        self.main_button = main_button
        self.fonts = fonts
        self.items = items
        self.current_idx = current_idx

        self.change_current_idx(current_idx)

    def change_current_idx(self, new_idx: int) -> None:
        """Change the current index."""
        if new_idx < 0 or new_idx >= len(self.fonts):
            raise IndexError(f"Index {new_idx} out of bounds for fonts list of length {len(self.fonts)}.")
        self.items[self.current_idx].classes(replace="bg-white text-black")
        self.items[new_idx].classes(replace="bg-primary text-white")
        self.current_idx = new_idx
        self.main_button.style(f'font-family: "{self.font.font_name}";')

    @property
    def font(self) -> CustomFont:
        """Return the selected font."""
        return self.fonts[self.current_idx]


def get_css_header(font: CustomFont) -> str | None:
    """Get the CSS header for the font."""
    font_path = font.value.get_file()
    if font_path is None or not isinstance(font_path, str):
        return None

    font_path = os.path.basename(font_path)
    if font_path.lower().endswith('.otf'):
        font_format = 'opentype'
    elif font_path.lower().endswith('.ttf'):
        font_format = 'truetype'
    else:
        raise ValueError("Unsupported font format. Please provide a .otf or .ttf file.")

    header = f'''
        @font-face {{
            font-family: '{font.font_name}';
            src: url('/fonts/{font_path}') format('{font_format}');
        }}
    '''
    return textwrap.dedent(header)
