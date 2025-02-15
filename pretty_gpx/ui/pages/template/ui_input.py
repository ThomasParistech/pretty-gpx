#!/usr/bin/python3
"""Ui Input."""
from collections.abc import Awaitable
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from typing import Self

from nicegui import ui
from typing_extensions import TypedDict

from pretty_gpx.common.utils.utils import safe


class DiscreteValue(TypedDict):
    """Structured representation of discrete values for dropdowns."""
    name: str
    priority: Any


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
        with ui.input(label=label, value=value).on('keydown.enter', on_enter).style('width: 100%') as input:
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
               discrete_val: list[str] | dict[Any, str],
               default_val: Any,
               tooltip: str,
               on_change: Callable[[], Awaitable[None]]) -> Self:
        """Create NiceGUI Dropdown select element and add a tooltip."""
        if isinstance(discrete_val, list):
            discrete_val = {val: val for val in discrete_val}

        assert isinstance(discrete_val, dict)
        assert default_val in list(discrete_val.keys())
        with ui.select(discrete_val,
                       label=label,
                       value=default_val).on('update:modelValue', on_change).style('width:100%') as input:
            ui.tooltip(tooltip)
        return cls(input)

    @property
    def _value_str(self) -> str:
        """Return the str value."""
        val = str(safe(self.input.value))
        return val

    @property
    def _value_raw(self) -> Any:
        """Return the str value."""
        val: Any = safe(self.input.value)
        return val


@dataclass
class UiDropdownStr(UiDropdown):
    """NiceGUI Str Dropdown Wrapper."""

    @property
    def value(self) -> str:
        """Return the value."""
        return self._value_str

@dataclass
class UiDropdownGeneric(UiDropdown):
    """NiceGUI Str Dropdown Wrapper."""

    @property
    def value(self) -> Any:
        """Return the value."""
        return self._value_raw

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
