#!/usr/bin/python3
"""NiceGUI Run."""
from collections.abc import Awaitable
from collections.abc import Callable
from typing import ParamSpec
from typing import TypeVar

from nicegui import run

from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.common.utils.profile import ProfilingEvent
from pretty_gpx.ui.utils.modal import UiWaitingModal

P = ParamSpec('P')
R = TypeVar('R')


def on_click_slow_action_in_other_thread(label: str,
                                         slow_func: Callable[..., tuple[R, list[ProfilingEvent]]],
                                         done_callback: Callable[[R], None] | None) -> Callable[[], Awaitable[None]]:
    """Callback to open a modal dialog and run a slow function in a separate thread.

    Args:
        label: The label of the modal dialog.
        slow_func: The function to run in a separate thread. Note it must have been decorated with @profile_parallel
            to correctly profile the execution.
        done_callback: The callback to call with the result of slow_func.

    Returns:
        An async function that shows a modal dialog, runs slow_func in a separate thread and calls done_callback with
        the result
    """
    async def on_click() -> None:
        with UiWaitingModal(label), Profiling.Scope("Modal"):
            res = await run_io_bound(slow_func)

            if done_callback is not None:
                done_callback(res)

    return on_click


async def run_cpu_bound(func: Callable[P, tuple[R, list[ProfilingEvent]]],
                        *args: P.args, **kwargs: P.kwargs) -> R:
    """Run a CPU-bound function (decorated with @profile_parallel) in a separate process."""
    # To run in a separate process, we need to transfer the whole state of the passed function to the process
    # (which is done with pickle). It is encouraged to create static methods (or free functions) which get all the data
    # as simple parameters (eg. no class/ui logic) and return the result (instead of writing it in class properties or
    # global variables).
    res, profiling_events = await run.cpu_bound(func, *args, **kwargs)
    Profiling.push_events(profiling_events)
    return res


async def run_io_bound(func: Callable[P, tuple[R, list[ProfilingEvent]]],
                       *args: P.args, **kwargs: P.kwargs) -> R:
    """Run an I/O-bound function (decorated with @profile_parallel) in a separate thread."""
    res, profiling_events = await run.io_bound(func, *args, **kwargs)
    Profiling.push_events(profiling_events)
    return res
