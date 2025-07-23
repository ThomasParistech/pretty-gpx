#!/usr/bin/python3
"""Ui Fonts Menu, to select a font from a list and also select a font size."""
from collections.abc import Awaitable
from collections.abc import Callable

from nicegui import ui

from pretty_gpx.common.drawing.utils.drawing_figure import A4Float
from pretty_gpx.common.drawing.utils.fonts import CustomFont
from pretty_gpx.ui.pages.template.ui_font_select import UiFontSelect


class UiFontAndSizeSelect:
    """NiceGui menu to select a font in a list and also select a font size."""

    def __init__(self, *,
                 label: str,
                 fonts: tuple[CustomFont, ...],
                 on_change: Callable[[], Awaitable[None]],
                 start_fontsize: A4Float,
                 start_font: CustomFont | None = None,
                 fontsize_geometric_step: float = 1.2) -> None:
        """Create a UiFontAndSizeSelect."""
        with ui.row().classes('items-center gap-2'):
            font_select = UiFontSelect(label=label,
                                       fonts=fonts,
                                       on_change=on_change,
                                       start_font=start_font)

            def on_click_minus() -> Callable[[], Awaitable[None]]:
                """On click minus handler."""
                async def handler() -> None:
                    self.fontsize /= fontsize_geometric_step
                    await on_change()
                return handler

            def on_click_plus() -> Callable[[], Awaitable[None]]:
                """On click plus handler."""
                async def handler() -> None:
                    self.fontsize *= fontsize_geometric_step
                    await on_change()
                return handler

            with ui.button(icon='remove', on_click=on_click_minus()
                           ).props('dense round').classes('bg-white text-black border border-black'):
                ui.tooltip('Decrease font size')
            with ui.button(icon='add', on_click=on_click_plus()
                           ).props('dense round').classes('bg-white text-black border border-black'):
                ui.tooltip('Increase font size')

        ###

        self.font_select = font_select
        self.fontsize = start_fontsize

    @property
    def font(self) -> CustomFont:
        """Return the selected font."""
        return self.font_select.font
