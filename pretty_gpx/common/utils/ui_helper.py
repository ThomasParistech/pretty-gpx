#!/usr/bin/python3
"""NiceGUI Helper."""
import asyncio
import concurrent.futures
from collections.abc import Callable

from nicegui import app
from nicegui import ui


class UiModal:
    """Context Manager for a modal dialog."""

    def __init__(self, label: str) -> None:
        self.label = label

    def __enter__(self):
        self.dialog = ui.dialog().props('persistent')
        self.dialog.open()
        with self.dialog, ui.card(), ui.row().classes('w-full items-center'):
            ui.label(self.label)
            ui.spinner(size='lg')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dialog.close()


def on_click_slow_action_in_other_thread(label: str,
                                         slow_func: Callable,
                                         done_callback: Callable | None) -> Callable:
    """Return an async function that runs slow_func in a separate thread and calls done_callback with the result."""
    async def on_click():
        with UiModal(label):
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                res = await loop.run_in_executor(pool, slow_func)

            if done_callback is not None:
                done_callback(res)

    return on_click


def shutdown_app_and_close_tab():
    """Shutdown the app and close the tab."""
    ui.run_javascript("window.close();")
    app.shutdown()
