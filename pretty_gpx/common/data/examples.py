#!/usr/bin/python3
"""GPX examples."""
import os
from enum import auto
from enum import Enum

from pretty_gpx.common.utils.paths import EXAMPLES_DIR


class CyclingGpx(Enum):
    """Cycling GPX examples."""
    AMBERIEU = auto()
    ANCIZAN_PEYRESOURDE_AZET_ASPIN = auto()
    COUILLOLE = auto()
    HAWAII = auto()
    MARMOTTE = auto()
    SOULOR_AUBISQUE_SPANDELLES = auto()
    VENTOUX = auto()

    @staticmethod
    def folder() -> str:
        """Return the folder where cycling GPX examples are stored."""
        return os.path.join(EXAMPLES_DIR, 'cycling')

    @property
    def path(self) -> str:
        """Path to the GPX file."""
        return os.path.join(self.folder(), f'{self.name.lower()}.gpx')


class HikingGpx(Enum):
    """Hiking GPX examples."""
    ARAILLE = auto()
    CABALIROS = auto()
    DIAGONALE_DES_FOUS = auto()
    UTMB = auto()
    VANOISE = auto()
    VANOISE_1 = auto()
    VANOISE_2 = auto()
    VANOISE_3 = auto()

    @staticmethod
    def folder() -> str:
        """Return the folder where hiking GPX examples are stored."""
        return os.path.join(EXAMPLES_DIR, 'hiking')

    @property
    def path(self) -> str:
        """Path to the GPX file."""
        return os.path.join(self.folder(), f'{self.name.lower()}.gpx')


class RunningGpx(Enum):
    """Running GPX examples."""
    HALF_MARATHON_DEAUVILLE = auto()
    MARATHON_BERLIN = auto()
    MARATHON_BORDEAUX = auto()
    MARATHON_CHICAGO = auto()
    MARATHON_LONDON = auto()
    MARATHON_NEW_YORK = auto()
    MARATHON_NICE_CANNES = auto()
    MARATHON_PARIS = auto()
    MARATHON_RENNES = auto()
    PARIS_VERSAILLES = auto()
    ROUTE_4_CHATEAUX = auto()
    TEN_K_PARIS = auto()

    @staticmethod
    def folder() -> str:
        """Return the folder where running GPX examples are stored."""
        return os.path.join(EXAMPLES_DIR, 'running')

    @property
    def path(self) -> str:
        """Path to the GPX file."""
        return os.path.join(self.folder(), f'{self.name.lower()}.gpx')
