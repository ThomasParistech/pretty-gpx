#!/usr/bin/python3
"""Cache handler for data collected over area defined by a GpxBounds."""
import hashlib
import os
from dataclasses import dataclass

from pathvalidate import sanitize_filename

from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.utils.paths import CACHE_DIR


@dataclass(kw_only=True)
class GpxDataCacheHandler:
    """Cache handler for data collected over area defined by a GpxBounds."""
    name: str
    extension: str

    def __post_init__(self) -> None:
        assert self.extension.startswith('.')

    def get_path(self, bounds: GpxBounds) -> str:
        """Get path to the corresponding cache file."""
        bounds_str = f"{bounds.lon_min:.4f},{bounds.lon_max:.4f},{bounds.lat_min:.4f},{bounds.lat_max:.4f}"
        bounds_hash = hashlib.sha256(bounds_str.encode('utf-8')).hexdigest()

        parent_folder = os.path.join(CACHE_DIR, sanitize_filename(self.name.lower()))
        basename = f"{bounds_hash}{self.extension}"

        os.makedirs(parent_folder, exist_ok=True)

        return os.path.join(parent_folder, basename)
