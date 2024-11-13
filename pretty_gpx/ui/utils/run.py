#!/usr/bin/python3
"""NiceGUI Run."""
from collections.abc import Callable
from types import TracebackType
from typing import ParamSpec
from typing import TypeVar

from nicegui import run
from nicegui import ui
from nicegui.run import SubprocessException

from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.common.utils.profile import ProfilingEvent
from pretty_gpx.common.utils.utils import safe

P = ParamSpec('P')
R = TypeVar('R')


async def run_cpu_bound_safe(msg: str, func: Callable[P, tuple[R, list[ProfilingEvent]]],
                             *args: P.args, **kwargs: P.kwargs) -> R:
    """Run a CPU-bound function (decorated with @profile_parallel) in a separate process."""
    return safe(await run_cpu_bound(msg, func, *args, **kwargs))


async def run_cpu_bound(msg: str, func: Callable[P, tuple[R, list[ProfilingEvent]]],
                        *args: P.args, **kwargs: P.kwargs) -> R | None:
    """Run an optionally failing CPU-bound function (decorated with @profile_parallel) in a separate process."""
    # To run in a separate process, we need to transfer the whole state of the passed function to the process
    # (which is done with pickle). It is encouraged to create static methods (or free functions) which get all the data
    # as simple parameters (eg. no class/ui logic) and return the result (instead of writing it in class properties or
    # global variables).
    res = None
    with UiWaitingModal(msg):
        try:
            res, profiling_events = await run.cpu_bound(func, *args, **kwargs)
        except SubprocessException as e:
            logger.error(f"Error while {msg}: {e}")
            ui.notify(f'Error while {msg}:\n{e.original_message}',
                      type='negative', multi_line=True, timeout=0, close_button='OK')

    Profiling.push_events(profiling_events)
    return res


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
