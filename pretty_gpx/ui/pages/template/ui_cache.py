#!/usr/bin/python3
"""Ui Cache."""
from dataclasses import dataclass
from typing import Generic
from typing import Self
from typing import TypeVar

from natsort import index_natsorted
from nicegui import events
from nicegui.elements.upload import Upload

from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.structure import AugmentedGpxData
from pretty_gpx.common.structure import DownloadData
from pretty_gpx.common.structure import Drawer
from pretty_gpx.common.utils.profile import profile_parallel
from pretty_gpx.common.utils.utils import safe
from pretty_gpx.ui.utils.run import run_cpu_bound
from pretty_gpx.ui.utils.run import run_cpu_bound_safe

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
            name = names[0]
        else:
            name = f'a {len(names)}-days track ({", ".join(names)})'

        return await cls.on_upload_bytes(contents, paper_size, name=name)

    @classmethod
    async def on_single_upload_events(cls, e: events.UploadEventArguments, paper_size: PaperSize) -> Self | None:
        """Process the uploaded file."""
        name = e.name
        content = e.content.read()
        assert isinstance(e.sender, Upload)
        e.sender.reset()

        return await cls.on_upload_bytes(content, paper_size, name=name)

    @classmethod
    async def on_upload_bytes(cls,
                              content: bytes | str | list[bytes] | list[str],
                              paper_size: PaperSize,
                              name: str) -> Self | None:
        """Pocess the files asynchronously to create the cache."""
        gpx_data = await run_cpu_bound(f"Loading GPX Data from {name}", cls.get_gpx_data, content)
        if gpx_data is None:
            return None

        download_data = await run_cpu_bound(f"Downloading Background Data for {name}",
                                            cls.get_download_data, gpx_data, paper_size)
        if download_data is None:
            return None

        return await run_cpu_bound(f"Processing Data for {name}",
                                   cls.from_gpx_and_download_data, gpx_data, download_data)

    async def on_paper_size_change(self, new_paper_size: PaperSize) -> Self:
        """Change the paper size."""
        cls = self.__class__
        name = f"{new_paper_size.name} Poster"
        download_data = await run_cpu_bound_safe(f"Downloading Background Data for {name}",
                                                 cls.get_download_data, self.safe_drawer.gpx_data, new_paper_size)
        return await run_cpu_bound_safe(f"Processing Data for {name}",
                                        cls.from_gpx_and_download_data, self.safe_drawer.gpx_data, download_data)

    @classmethod
    @profile_parallel
    def get_gpx_data(cls, b: bytes | str | list[bytes] | list[str]) -> AugmentedGpxData:
        """Process the GPX file(s) to get AugmentedGpxData."""
        gpx_data_cls = cls.get_drawer_cls().get_gpx_data_cls()
        assert issubclass(gpx_data_cls, AugmentedGpxData)
        if isinstance(b, list):
            return gpx_data_cls.from_paths(b)
        return gpx_data_cls.from_path(b)

    @classmethod
    @profile_parallel
    def get_download_data(cls, gpx_data: AugmentedGpxData, paper_size: PaperSize) -> DownloadData:
        """Download the data."""
        download_data_cls = cls.get_drawer_cls().get_download_data_cls()
        assert issubclass(download_data_cls, DownloadData)
        return download_data_cls.from_gpx_and_paper_size(gpx_data, paper_size)

    @classmethod
    @profile_parallel
    def from_gpx_and_download_data(cls, gpx_data: AugmentedGpxData, download_data: DownloadData) -> Self:
        """Create the Drawer from the GPX and Download Data."""
        return cls(cls.get_drawer_cls().from_gpx_and_download_data(gpx_data, download_data))
