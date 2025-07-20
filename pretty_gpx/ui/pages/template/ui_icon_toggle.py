#!/usr/bin/python3
"""Ui Icon Toggle, to the let the user trigger an action by selecting an icon."""
import os
from collections.abc import Awaitable
from collections.abc import Callable

from nicegui import app
from nicegui import ui

from pretty_gpx.common.drawing.utils.plt_marker import MarkerType
from pretty_gpx.common.utils.paths import ICONS_DIR

app.add_static_files('/static', os.path.abspath(ICONS_DIR))


class UiIconToggle:
    """NiceGUI Icon Toggle.

    This component is used to the let the user trigger an action by selecting an icon.

    This UI toggle displays a row of buttons, each represented by an icon loaded 
    from a corresponding SVG file. The icons are linked to values of type `MarkerType`.

    When a button is clicked, the selected icon is visually highlighted, and a 
    provided async callback (`on_change`) is triggered. The currently selected 
    value can be accessed via the `value` property.
    """

    def __init__(self,
                 markers: list[MarkerType],
                 start_idx: int = 0,
                 *, on_change: Callable[[], Awaitable[None]]) -> None:
        self.markers = markers
        with ui.row().classes('items-center').style('gap: 0;'):
            self.buttons = [ui.button(icon=f"img:/static/{marker.name.lower():}.svg",
                                      on_click=self.on_click_idx(idx)).style('border-radius: 0;').props("color=white")
                            for idx, marker in enumerate(markers)]

        self.current_idx = start_idx
        self.buttons[start_idx].props("color=primary")

        self.on_change = on_change

    def on_click_idx(self, idx: int) -> Callable[[], Awaitable[None]]:
        """On click handler."""
        async def handler() -> None:
            self.buttons[self.current_idx].props("color=white")
            self.buttons[idx].props("color=primary")
            self.current_idx = idx
            await self.on_change()
        return handler

    @property
    def value(self) -> MarkerType:
        """Return the value."""
        return self.markers[self.current_idx]
