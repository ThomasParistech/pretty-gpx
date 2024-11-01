#!/usr/bin/python3
"""Ui Input."""
from collections.abc import Awaitable
from collections.abc import Callable
from dataclasses import dataclass

from nicegui import ui
from typing_extensions import Self

from pretty_gpx.common.utils.utils import safe


@dataclass
class UiInput:
    """NiceGUI Input Wrapper."""
    input: ui.input

    @classmethod
    def create(cls,
               *,
               label: str,
               value: str,
               tooltip: str,
               on_enter: Callable[[], Awaitable[None]]) -> Self:
        """Create NiceGUI Input element and add a tooltip."""
        with ui.input(label=label, value=value).on('keydown.enter', on_enter) as input:
            ui.tooltip(tooltip)
        return cls(input)

    @property
    def _value_str(self) -> str | None:
        """Return the str value."""
        val = str(safe(self.input.value))
        return val if val != "" else None


@dataclass
class UiInputStr(UiInput):
    """NiceGUI Str Input Wrapper."""

    @property
    def value(self) -> str | None:
        """Return the value."""
        return self._value_str


@dataclass
class UiInputFloat(UiInput):
    """NiceGUI Float Input Wrapper."""

    @property
    def value(self) -> float | None:
        """Return the value."""
        val = self._value_str
        if val is None:
            return None
        return float(val)


@dataclass
class UiInputInt(UiInput):
    """NiceGUI Int Input Wrapper."""

    @property
    def value(self) -> int | None:
        """Return the value."""
        val = self._value_str
        if val is None:
            return None
        return int(float(val))
