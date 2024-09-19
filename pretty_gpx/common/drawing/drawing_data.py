#!/usr/bin/python3
"""Drawing Data."""
from dataclasses import dataclass
from dataclasses import fields
from typing import Literal

from matplotlib.axes import Axes
from matplotlib.collections import LineCollection
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path


@dataclass(kw_only=True, init=False)
class BaseDrawingData:
    """Base Drawing Annotations."""

    def plot(self, ax: Axes, color: str) -> None:
        """Plot the annotation."""
        raise NotImplementedError("Plot method must be implemented in child classes")

    def kwargs(self, skip_xy: bool = False) -> dict:
        """Return the dataclass fields as a dictionary."""
        # Don't use asdict(self) as it will return a deepcopy of all non-dataclass fields, which is pretty slow
        return {f.name: getattr(self, f.name)
                for f in fields(self)
                if not (skip_xy and f.name in ('x', 'y'))}


@dataclass(kw_only=True)
class TextData(BaseDrawingData):
    """Text Data."""
    x: float
    y: float

    s: str

    fontsize: float
    fontproperties: FontProperties
    ha: str

    def plot(self, ax: Axes, color: str) -> None:
        """Plot the annotation."""
        ax.text(**self.kwargs(), c=color)


@dataclass(kw_only=True)
class PlotData(BaseDrawingData):
    """Line plot Data."""
    x: list[float]
    y: list[float]

    linewidth: float
    linestyle: Literal["solid", "dashed", "dashdot", "dotted"] = "solid"

    def plot(self, ax: Axes, color: str) -> None:
        """Plot the annotation."""
        ax.plot(self.x, self.y, **self.kwargs(skip_xy=True), c=color)


@dataclass(kw_only=True)
class ScatterData(BaseDrawingData):
    """Scatter Data."""
    x: list[float]
    y: list[float]

    marker: str | Path
    markersize: float

    def plot(self, ax: Axes, color: str) -> None:
        """Plot the annotation."""
        ax.plot(self.x, self.y, **self.kwargs(skip_xy=True),
                linestyle='', clip_on=False,  # Allow start/end markers to be drawn outside the plot area
                c=color)


@dataclass
class PolyFillData(BaseDrawingData):
    """Polygon Fill Data."""
    x: list[float]
    y: list[float]

    def plot(self, ax: Axes, color: str) -> None:
        """Plot the annotation."""
        ax.fill(self.x, self.y, **self.kwargs(skip_xy=True), c=color)


@dataclass
class LineCollectionData(BaseDrawingData):
    """LineCollection Data."""
    segments: list[list[tuple[float, float]]]

    linewidth: float

    def plot(self, ax: Axes, color: str) -> None:
        """Plot the annotation."""
        ax.add_collection(LineCollection(**self.kwargs(), colors=color))
