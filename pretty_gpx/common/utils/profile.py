#!/usr/bin/python3
"""Profiler Decorator."""
import inspect
import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from queue import Queue
from types import TracebackType
from typing import ParamSpec
from typing import TypeVar

from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.paths import DATA_DIR
from pretty_gpx.common.utils.utils import safe

PROFILE = True


@dataclass(kw_only=True)
class ProfilingEvent:
    """Profiling Event."""
    name: str
    context_name: str
    start_time: float
    end_time: float


class Profiling:
    """Profiling class.

    Either use the @profile decorator to profile a function
    or use the Profiling.Scope context manager to profile a block of code

    Don't forget to call Profiling.export_events() to dump the profiling results
    """

    __t0: float = time.perf_counter()
    __main_queue: Queue[ProfilingEvent] = Queue()

    __bypass_name: str | None = None
    __bypass_queue: Queue[ProfilingEvent]

    def __init__(self) -> None:
        raise NotImplementedError()

    @staticmethod
    def push_event(name: str, start_time: float, end_time: float) -> None:
        """Push profiling event."""
        if Profiling.__bypass_name is not None:
            queue = safe(Profiling.__bypass_queue)
            context_name = Profiling.__bypass_name
        else:
            queue = Profiling.__main_queue
            context_name = "Main"

        # Queue is thread-safe
        queue.put(ProfilingEvent(name=name,
                                 context_name=context_name,
                                 start_time=start_time-Profiling.__t0,
                                 end_time=end_time-Profiling.__t0))

    @staticmethod
    def push_events(events: list[ProfilingEvent]) -> None:
        """Push a queue of events."""
        for e in events:
            Profiling.__main_queue.put(e)

    @staticmethod
    def set_bypass_queue(name: str) -> None:
        """Set the bypass queue."""
        assert Profiling.__bypass_name is None, \
            f"Bypass queue named '{Profiling.__bypass_name}' is already set. Pop it first"
        Profiling.__bypass_name = name
        Profiling.__bypass_queue = Queue()

    @staticmethod
    def pop_bypass_queue() -> list[ProfilingEvent]:
        """Pop the bypass queue."""
        assert Profiling.__bypass_name is not None
        data_to_process = []
        while not Profiling.__bypass_queue.empty():
            data_to_process.append(Profiling.__bypass_queue.get())
        Profiling.__bypass_name = None

        return data_to_process

    @staticmethod
    def export_events(output_path: str = os.path.join(DATA_DIR, 'profile.json')) -> None:
        """Dump profiling events into a JSON file that can be provided to the Chrome Tracing Viewer."""
        if not PROFILE:
            return

        events: list[dict[str, str | int | float]] = []

        assert Profiling.__bypass_name is None

        while not Profiling.__main_queue.empty():
            e = Profiling.__main_queue.get()
            events.append({"name": e.name, "ph": "B", "ts": e.start_time*1e6, "tid": e.context_name, "pid": 0})
            events.append({"name": e.name, "ph": "E", "ts": e.end_time*1e6, "tid": e.context_name, "pid": 0})

        with open(output_path, "w", encoding="utf-8") as _f:
            json.dump({"traceEvents": events}, _f)

        logger.info(f"Open Chrome, type chrome://tracing/ and load the file located at {os.path.abspath(output_path)}")

    class Scope:
        """Profile the scope.

        Use as context `with Profiling.Scope(name):`

        It's also possible to retrieve the time (s) spent inside the scope:

        ```
        with Profiling.Scope(name) as scope:
            ...

        print(scope.dt)
        ```
        """

        def __init__(self, name: str):
            self._name = name
            self._dt: float | None = None

        @property
        def dt(self) -> float:
            """Returns time (s) spent inside the scope."""
            return safe(self._dt)

        def __enter__(self) -> 'Profiling.Scope':
            self._start: float = time.perf_counter()
            return self

        def __exit__(self,
                     exc_type: type[BaseException] | None,
                     exc_val: BaseException | None,
                     exc_tb: TracebackType | None) -> None:
            self._dt = time.perf_counter() - self._start
            Profiling.push_event(self._name, self._start, self._start+self._dt)


P = ParamSpec('P')
R = TypeVar('R')


def profile(func: Callable[P, R]) -> Callable[P, R]:
    """Profiling decorator."""
    # Warning: This decorator won't work if the function runs inside a multiprocessing Process
    # Processes are not like threads; they do not share memory, which means the global variables are copied and not
    # modified outside the scope of the process
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        with Profiling.Scope(get_function_name(func)):
            return func(*args, **kwargs)

    return wrapper


def profile_parallel(func: Callable[P, R]) -> Callable[P, tuple[R, list[ProfilingEvent]]]:
    """Decorator to profile a function that runs in parallel."""
    # Events pushed to the Profiling queue in a multiprocessing Process are lost, because all the data is copied
    # and not shared between processes.
    # To solve this, we store the events in a bypass queue and pop them after the function has been executed
    # to push them to the main queue

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> tuple[R, list[ProfilingEvent]]:
        Profiling.set_bypass_queue("Parallel")
        with Profiling.Scope(get_function_name(func)):
            retval = func(*args, **kwargs)
        events = Profiling.pop_bypass_queue()
        return retval, events
    return wrapper


def get_function_name(func: Callable) -> str:
    """Get file and function name."""
    module_name = func.__module__.split('.')[-1]
    if module_name == "__main__":
        if isinstance(func, staticmethod):
            module_name = func.__qualname__.split(".")[0]
        else:
            module_name = os.path.splitext(os.path.basename(inspect.getfile(func)))[0]
    return f"{module_name}::{func.__name__}"
