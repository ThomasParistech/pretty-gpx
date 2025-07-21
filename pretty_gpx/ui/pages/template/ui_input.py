#!/usr/bin/python3
"""Ui Input, to capture text input from the user."""
import os
from collections.abc import Awaitable
from collections.abc import Callable
from dataclasses import dataclass
from typing import Self

from nicegui import app
from nicegui import ui

from pretty_gpx.common.utils.paths import FONTS_DIR
from pretty_gpx.common.utils.utils import safe

app.add_static_files('/fonts', os.path.abspath(FONTS_DIR))


@dataclass
class UiInput:
    """NiceGUI Input Wrapper.

    This component is used to capture text input from the user.
    """
    input: ui.input

    @classmethod
    def create(cls,
               *,
               label: str,
               value: str,
               tooltip: str,
               on_enter: Callable[[], Awaitable[None]]) -> Self:
        """Create NiceGUI Input element and add a tooltip."""
        with ui.input(label=label, value=value).on('keydown.enter', on_enter).style('width: 100%') as input:
            ui.tooltip(tooltip)
        return cls(input)

    @property
    def _value_str(self) -> str | None:
        """Return the str value."""
        val = str(safe(self.input.value))
        return val if val != "" else None


@dataclass
class UiInputStr(UiInput):
    """NiceGUI Str Input Wrapper.

    This component is used to capture text input from the user as a string.
    """

    @property
    def value(self) -> str | None:
        """Return the value."""
        return self._value_str


@dataclass
class UiInputFloat(UiInput):
    """NiceGUI Float Input Wrapper.

    This component is used to capture text input from the user as a float.
    """

    @property
    def value(self) -> float | None:
        """Return the value."""
        val = self._value_str
        if val is None:
            return None
        return float(val)


@dataclass
class UiInputInt(UiInput):
    """NiceGUI Int Input Wrapper.

    This component is used to capture text input from the user as an int.
    """

    @property
    def value(self) -> int | None:
        """Return the value."""
        val = self._value_str
        if val is None:
            return None
        return int(float(val))
