#!/usr/bin/python3
"""Ui Select that lets the user select one option from multiple choices."""
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


@dataclass
class UiSelect(Generic[T]):
    """NiceGUI Select Wrapper.

    Similar to `UiToggle`, this component is used to let the user select one option from multiple choices.
    The only difference is that this component uses a select dropdown instead of a toggle.
    """
    select: ui.select
    mapping: dict[str, T]

    @property
    def value(self) -> T:
        """Return the value."""
        return self.mapping[str(safe(self.select.value))]

    @classmethod
    def create(cls,
               mapping: dict[str, T],
               *,
               label: str,
               tooltip: str,
               on_change: Callable[[], Awaitable[None]],
               start_key: str | None = None) -> Self:
        """Create a new UiToggle from a list of possible named values."""
        keys = list(mapping.keys())
        if start_key is None:
            start_key = keys[0]
        assert_in(start_key, keys)
        with ui.select(keys,
                       label=label,
                       value=start_key).on('update:modelValue', on_change).style('width:100%') as select:
            ui.tooltip(tooltip)
        return cls(select, mapping)
