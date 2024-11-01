#!/usr/bin/python3
"""Ui Cache."""
from dataclasses import dataclass
from typing import Generic
from typing import TypeVar

from natsort import index_natsorted
from nicegui import events
from nicegui import ui
from nicegui.elements.upload import Upload
from nicegui.run import SubprocessException
from typing_extensions import Self

from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import profile_parallel
from pretty_gpx.common.utils.utils import safe
from pretty_gpx.ui.utils.run import run_cpu_bound
from pretty_gpx.ui.utils.run import UiWaitingModal

T = TypeVar('T')


@dataclass(init=False)
class UiCache(Generic[T]):
    """UI Cache Management.

    The methods `on_multi_upload_events` and `on_single_upload_events` serve as callbacks for the `ui.upload` component
    used in the class `UiManager`.
    The cache is initialized as `None` and is populated when files are uploaded, and updated upon paper size changes.

    Subclasses must implement:
    - `on_multi_upload_events` or `on_single_upload_events`
    - `on_paper_size_change`
    """
    data: T | None = None

    @classmethod
    def multi(cls) -> bool:
        """Detect if the child class is for multi-upload."""
        single = 'process_file' in cls.__dict__
        multi = 'process_files' in cls.__dict__
        assert multi != single, "Either process_file or process_files must be implemented"
        return multi

    @property
    def safe_data(self) -> T:
        """Return the safe data."""
        return safe(self.data)

    def is_initialized(self) -> bool:
        """Check if the cache is initialized."""
        return self.data is not None

    @classmethod
    async def on_multi_upload_events(cls, e: events.MultiUploadEventArguments,
                                     paper_size: PaperSize) -> Self | None:
        """Sort the uploaded files by name and process them."""
        sorted_indices = index_natsorted(e.names)
        names = [e.names[i] for i in sorted_indices]
        contents = [e.contents[i].read() for i in sorted_indices]
        assert isinstance(e.sender, Upload)
        e.sender.reset()

        if len(contents) == 1:
            msg = f"Processing {names[0]}"
        else:
            msg = f'Processing a {len(names)}-days track ({", ".join(names)})'

        return await cls.on_upload_bytes(contents, paper_size, msg)

    @classmethod
    async def on_single_upload_events(cls, e: events.UploadEventArguments, paper_size: PaperSize) -> Self | None:
        """Process the uploaded file."""
        name = e.name
        content = e.content.read()
        assert isinstance(e.sender, Upload)
        e.sender.reset()

        return await cls.on_upload_bytes(content, paper_size, msg=f"Processing {name}")

    @classmethod
    async def on_upload_bytes(cls,
                              content: bytes | str | list[bytes] | list[str],
                              paper_size: PaperSize,
                              msg: str) -> Self | None:
        """Pocess the files asynchronously to create the cache."""
        with UiWaitingModal(msg):
            try:
                if isinstance(content, list):
                    return await run_cpu_bound(cls.process_files, content, paper_size)
                return await run_cpu_bound(cls.process_file, content, paper_size)
            except SubprocessException as e:
                logger.error(f"Error while {msg}: {e}")
                logger.warning("Skip processing uploaded files")
                ui.notify(f'Error while {msg}:\n{e.original_message}',
                          type='negative', multi_line=True, timeout=0, close_button='OK')
                return None

    async def on_paper_size_change(self, new_paper_size: PaperSize) -> Self:
        """Change the paper size."""
        with UiWaitingModal(f"Creating {new_paper_size.name} Poster"):
            return await run_cpu_bound(self.change_paper_size, new_paper_size)

    ############

    @profile_parallel
    def change_paper_size(self, new_paper_size: PaperSize) -> Self:
        """Change the paper size."""
        raise NotImplementedError

    @classmethod
    @profile_parallel
    def process_file(cls, b: bytes | str, paper_size: PaperSize) -> Self:
        """Process the GPX file."""
        raise NotImplementedError

    @classmethod
    @profile_parallel
    def process_files(cls, list_b: list[bytes] | list[str], paper_size: PaperSize) -> Self:
        """Process the GPX files."""
        raise NotImplementedError
