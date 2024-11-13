#!/usr/bin/python3
"""Structure."""
from dataclasses import dataclass
from typing import Generic
from typing import Self
from typing import TypeVar

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pretty_gpx.common.drawing.base_drawing_figure import BaseDrawingFigure
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.layout.paper_size import PaperSize


@dataclass(init=False)
class AugmentedGpxData:
    """Augmented GPX Data."""
    track: GpxTrack

    ######### METHODS TO IMPLEMENT #########

    @classmethod
    def from_path(cls, path: str | bytes) -> Self:
        """Create an AugmentedGpxData from a GPX file."""
        raise NotImplementedError

    @classmethod
    def from_paths(cls, paths: str | bytes | list[str] | list[bytes]) -> Self:
        """Create an AugmentedGpxData from GPX files."""
        raise NotImplementedError

    #########################################


@dataclass
class DownloadData:
    """Download Data."""

    bounds: GpxBounds

    ######### METHODS TO IMPLEMENT #########

    @classmethod
    def from_gpx_and_paper_size(cls: type[Self], gpx_data: AugmentedGpxData, paper: PaperSize) -> Self:
        """Init the DownloadData from GPX data and Paper Size."""
        raise NotImplementedError

    #########################################


@dataclass(frozen=True, init=False)
class DrawingInputs:
    """Drawing Inputs."""


@dataclass(frozen=True, init=False)
class DrawingParams:
    """Drawing Params."""


T = TypeVar('T', bound='AugmentedGpxData')
U = TypeVar('U', bound='DownloadData')
V = TypeVar('V', bound='DrawingInputs')
W = TypeVar('W', bound='DrawingParams')


@dataclass(init=False)
class DrawingFigure(BaseDrawingFigure, Generic[W]):
    """Drawing Figure, handling the setup of the figure and the drawing of the data."""

    ######### METHODS TO IMPLEMENT #########

    def draw(self, fig: Figure, ax: Axes, params: W) -> None:
        """Draw the figure."""
        raise NotImplementedError

    #########################################


@dataclass
class Drawer(Generic[T, U, V, W]):
    """Drawer."""

    gpx_data: T
    plotter: DrawingFigure[W]

    ######### METHODS TO IMPLEMENT #########

    @staticmethod
    def get_gpx_data_cls() -> type[T]:
        """Return the template AugmentedGpxData class (Because Python doesn't allow to use T as a type)."""
        raise NotImplementedError

    @staticmethod
    def get_download_data_cls() -> type[U]:
        """Return the template DownloadData class (Because Python doesn't allow to use U as a type)."""
        raise NotImplementedError

    @classmethod
    def from_gpx_and_download_data(cls, gpx_data: T, download_data: U) -> Self:
        """Create a Drawer from GPX data and Download Data."""
        raise NotImplementedError

    def get_params(self, inputs: V) -> W:
        """Convert DrawingInputs to DrawingParams."""
        raise NotImplementedError

    #########################################

    # @classmethod
    # def from_path(cls, path: str | bytes, paper: PaperSize) -> Self:
    #     """Create a Drawer from a GPX file."""
    #     gpx_data = cls.get_gpx_data_cls().from_path(path)
    #     return cls.from_gpx_data(gpx_data, paper)

    # @classmethod
    # def from_paths(cls, paths: str | bytes | list[str] | list[bytes], paper: PaperSize) -> Self:
    #     """Create a Drawer from GPX files."""
    #     gpx_data = cls.get_gpx_data_cls().from_paths(paths)
    #     return cls.from_gpx_data(gpx_data, paper)

    def draw(self, fig: Figure, ax: Axes, inputs: V) -> None:
        """Convert DrawingParams to DrawingData and draw the figure."""
        data = self.get_params(inputs)
        self.plotter.draw(fig, ax, data)
