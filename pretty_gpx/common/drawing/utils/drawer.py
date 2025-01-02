#!/usr/bin/python3
"""Parent class for poster drawers."""
from abc import ABC
from abc import abstractmethod

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pretty_gpx.common.layout.paper_size import PaperSize


class DrawerBase(ABC):
    """Base Drawer class for posters."""
    @abstractmethod
    def change_papersize(self, paper: PaperSize) -> None:
        """Change Papersize of the poster."""
        ...

    @abstractmethod
    def draw(self, fig: Figure, ax: Axes, high_resolution: bool) -> None:
        """Draw the poster on the given figure and axes (in high resolution if requested)."""
        ...


class DrawerSingleTrack(DrawerBase, ABC):
    """Base Drawer class for Single-Track posters."""
    @abstractmethod
    def change_gpx(self, gpx_path: str | bytes, paper: PaperSize) -> None:
        """Load a single GPX file to create a Multi-Track poster."""
        ...


class DrawerMultiTrack(DrawerBase, ABC):
    """Base Drawer class for Multi-Track posters."""
    @abstractmethod
    def change_gpx(self, gpx_path: list[str] | list[bytes], paper: PaperSize) -> None:
        """Load several GPX files to create a Multi-Track poster."""
        ...
