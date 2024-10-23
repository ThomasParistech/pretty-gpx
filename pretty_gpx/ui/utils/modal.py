#!/usr/bin/python3
"""NiceGUI Modal."""
from types import TracebackType

from nicegui import ui


class UiWaitingModal:
    """Context Manager for a waiting modal dialog."""

    def __init__(self, label: str) -> None:
        self.label = label

    def __enter__(self) -> None:
        self.dialog = ui.dialog().props('persistent')
        self.dialog.open()
        with self.dialog, ui.card(), ui.row().classes('w-full items-center'):
            ui.label(self.label)
            ui.spinner(size='lg')

    def __exit__(self,
                 exc_type: type[BaseException] | None,
                 exc_val: BaseException | None,
                 exc_tb: TracebackType | None) -> None:
        self.dialog.close()
