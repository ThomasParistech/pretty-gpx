#!/usr/bin/python3
"""Paper Size."""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PaperSize:
    """Paper Size."""
    w_mm: int
    h_mm: int
    margin_mm: int
    name: str

    @property
    def diag_mm(self) -> float:
        """Diagonal in mm."""
        return math.sqrt(self.w_mm**2 + self.h_mm**2)


PAPER_SIZES: dict[str, PaperSize] = {
    paper.name: paper
    for paper in [PaperSize(w_mm=210, h_mm=297, margin_mm=10, name="A4"),
                  PaperSize(w_mm=300, h_mm=400, margin_mm=15, name="30x40"),
                  PaperSize(w_mm=320, h_mm=320, margin_mm=15, name="32x32"),
                  PaperSize(w_mm=500, h_mm=700, margin_mm=25, name="50x70"),
                  PaperSize(w_mm=400, h_mm=300, margin_mm=15, name="40x30")]
}
