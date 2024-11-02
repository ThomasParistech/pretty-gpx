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
from pretty_gpx.common.structure import Drawer
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import profile_parallel
from pretty_gpx.common.utils.utils import safe
from pretty_gpx.ui.utils.modal import UiWaitingModal
from pretty_gpx.ui.utils.run import run_cpu_bound

T = TypeVar('T', bound='Drawer')


@dataclass
class UiCache(Generic[T]):
    """UI Cache Management.

    The methods `on_multi_upload_events` and `on_single_upload_events` serve as callbacks for the `ui.upload` component
    used in the class `UiManager`.
    The cache is initialized as `None` and is populated when files are uploaded, and updated upon paper size changes.

    The `Drawer` class inits an AugmentedGpxData and a DrawingFigure from GPX file(s), and has a `draw` method to
    draw the poster on a Matplotlib Figure.
    """

    drawer: T | None = None

    ######### METHODS TO IMPLEMENT #########

    @staticmethod
    def get_drawer_cls() -> type[T]:
        """Return the template Drawer class (Because Python doesn't allow to use T as a type)."""
        raise NotImplementedError

    #########################################

    @classmethod
    def multi(cls) -> bool:
        """Detect if the child class is for multi-upload."""
        gpx_data_cls = cls.get_drawer_cls().get_gpx_data_cls()
        single = 'from_path' in gpx_data_cls.__dict__
        multi = 'from_paths' in gpx_data_cls.__dict__
        assert multi != single, "Either from_path or from_paths must be implemented " \
            f"inside the AugmentedGpxData class ({gpx_data_cls.__class__.__name__})"
        return multi

    @property
    def safe_drawer(self) -> T:
        """Return the safe Drawer."""
        return safe(self.drawer)

    def is_initialized(self) -> bool:
        """Check if the cache is initialized."""
        return self.drawer is not None

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
        res = None
        with UiWaitingModal(msg):
            try:
                if isinstance(content, list):
                    res = await run_cpu_bound(cls.process_files, content, paper_size)
                else:
                    res = await run_cpu_bound(cls.process_file, content, paper_size)
            except SubprocessException as e:
                logger.error(f"Error while {msg}: {e}")
                logger.warning("Skip processing uploaded files")
                ui.notify(f'Error while {msg}:\n{e.original_message}',
                          type='negative', multi_line=True, timeout=0, close_button='OK')

        return res

    async def on_paper_size_change(self, new_paper_size: PaperSize) -> Self:
        """Change the paper size."""
        with UiWaitingModal(f"Creating {new_paper_size.name} Poster"):
            return await run_cpu_bound(self.change_paper_size, new_paper_size)

    @profile_parallel
    def change_paper_size(self, new_paper_size: PaperSize) -> Self:
        """Change the paper size."""
        cls = self.__class__
        return cls(cls.get_drawer_cls().from_gpx_data(self.safe_drawer.gpx_data, new_paper_size))

    @classmethod
    @profile_parallel
    def process_file(cls, b: bytes | str, paper_size: PaperSize) -> Self:
        """Process the GPX file."""
        return cls(cls.get_drawer_cls().from_path(b, paper_size))

    @classmethod
    @profile_parallel
    def process_files(cls, list_b: list[bytes] | list[str], paper_size: PaperSize) -> Self:
        """Process the GPX files."""
        return cls(cls.get_drawer_cls().from_paths(list_b, paper_size))
