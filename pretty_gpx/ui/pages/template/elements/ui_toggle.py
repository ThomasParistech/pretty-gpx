#!/usr/bin/python3
"""Ui Toggle."""
from collections.abc import Awaitable
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic
from typing import TypeVar

from nicegui import ui
from typing_extensions import Self

from pretty_gpx.common.utils.utils import safe

T = TypeVar('T')
U = TypeVar('U')


@dataclass
class UiToggle(Generic[T]):
    """NiceGUI Toggle Wrapper."""
    toggle: ui.toggle
    mapping: dict[str, T]

    @property
    def value(self) -> T:
        """Return the value."""
        return self.mapping[str(safe(self.toggle.value))]

    @classmethod
    def create(cls, mapping: dict[str, T], *, on_change: Callable[[], Awaitable[None]]) -> Self:
        """Create a new UiToggle from a list of possible named values."""
        keys = list(mapping.keys())
        toggle = ui.toggle(keys, value=keys[0], on_change=on_change)
        return cls(toggle, mapping)

    def change(self, new_mapping: dict[str, U]) -> 'UiToggle[U]':
        """Change the mapping."""
        new_keys = list(new_mapping.keys())
        self.toggle.options = new_keys
        self.toggle.value = self.toggle.options[0]
        self.toggle.update()
        return UiToggle[U](self.toggle, new_mapping)
