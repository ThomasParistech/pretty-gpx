#!/usr/bin/python3
"""Ui Input."""
from collections.abc import Awaitable
from collections.abc import Callable
from dataclasses import dataclass
from typing import Self

from nicegui import ui

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
class UiDropdown:
    """NiceGUI Input Wrapper."""
    input: ui.select

    @classmethod
    def create(cls,
               *,
               label: str,
               discrete_val: list[str],
               default_idx: int, 
               tooltip: str,
               on_change: Callable[[], Awaitable[None]]) -> Self:
        """Create NiceGUI Dropdown select element and add a tooltip."""
        with ui.select(discrete_val,
                       label=label,
                       value=discrete_val[default_idx]).on('update:modelValue', on_change) as input:
            ui.tooltip(tooltip)
        return cls(input)

    @property
    def _value_str(self) -> str:
        """Return the str value."""
        val = str(safe(self.input.value))
        return val


@dataclass
class UiDropdownStr(UiDropdown):
    """NiceGUI Str Dropdown Wrapper."""

    @property
    def value(self) -> str:
        """Return the value."""
        return self._value_str


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
