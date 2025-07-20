#!/usr/bin/python3
"""UI toggle that lets the user select one option from multiple choices."""
from collections.abc import Awaitable
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic
from typing import Self
from typing import TypeVar

from nicegui import ui

from pretty_gpx.common.utils.asserts import assert_in
from pretty_gpx.common.utils.utils import safe

T = TypeVar('T')
U = TypeVar('U')


@dataclass
class UiToggle(Generic[T]):
    """NiceGUI Toggle Wrapper.

    This component is used to let the user select one option from multiple choices.

    It displays a toggle with user-friendly labels, while internally mapping each
    label to a value of any type `T`. It allows complex data (not just strings) 
    to be associated with each toggle option.

    You provide a mapping from labels to values when creating the component. The user
    interacts with the labels, and the corresponding typed value can be accessed via
    the `value` property.

    When an option is clicked, the selected name is visually highlighted, and a 
    provided async callback (`on_change`) is triggered.
    """
    toggle: ui.toggle
    mapping: dict[str, T]

    @property
    def value(self) -> T:
        """Return the value."""
        return self.mapping[str(safe(self.toggle.value))]

    @classmethod
    def create(cls,
               mapping: dict[str, T],
               *,
               tooltip: str,
               on_change: Callable[[], Awaitable[None]],
               start_key: str | None = None) -> Self:
        """Create a new UiToggle from a list of possible named values."""
        keys = list(mapping.keys())
        if start_key is None:
            start_key = keys[0]
        assert_in(start_key, keys)
        with ui.toggle(keys, value=start_key, on_change=on_change) as toggle:
            ui.tooltip(tooltip)
        return cls(toggle, mapping)

    def change(self, new_mapping: dict[str, U]) -> 'UiToggle[U]':
        """Change the mapping."""
        new_keys = list(new_mapping.keys())
        self.toggle.options = new_keys
        self.toggle.value = self.toggle.options[0]
        self.toggle.update()
        return UiToggle[U](self.toggle, new_mapping)
