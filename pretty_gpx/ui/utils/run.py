#!/usr/bin/python3
"""NiceGUI Run."""
from collections.abc import Callable
from typing import ParamSpec
from typing import TypeVar

from nicegui import run

from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.common.utils.profile import ProfilingEvent

P = ParamSpec('P')
R = TypeVar('R')


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
