#!/usr/bin/python3
"""Fonts."""
import os
from enum import Enum
from typing import Final

from matplotlib.font_manager import FontProperties

from pretty_gpx.common.utils.paths import FONTS_DIR


class CustomFont(Enum):
    """Custom Fonts Enum."""
    DEJA_VU_SANS_BOLD = FontProperties(weight="bold")
    MONTSERRAT_REGULAR = FontProperties(fname=os.path.join(FONTS_DIR, "Montserrat-Regular.ttf"))
    MONTSERRAT_SEMIBOLD = FontProperties(fname=os.path.join(FONTS_DIR, "Montserrat-SemiBold.ttf"))
    INTER_REGULAR = FontProperties(fname=os.path.join(FONTS_DIR, "Inter-Regular.ttf"))
    INTER_SEMIBOLD = FontProperties(fname=os.path.join(FONTS_DIR, "Inter-SemiBold.ttf"))
    MANROPE_REGULAR = FontProperties(fname=os.path.join(FONTS_DIR, "Manrope-Regular.ttf"))
    MANROPE_SEMIBOLD = FontProperties(fname=os.path.join(FONTS_DIR, "Manrope-SemiBold.ttf"))
    LOBSTER = FontProperties(fname=os.path.join(FONTS_DIR, "Lobster.ttf"))
    MONOTON = FontProperties(fname=os.path.join(FONTS_DIR, "Monoton.ttf"))
    GOCHI_HAND = FontProperties(fname=os.path.join(FONTS_DIR, "GochiHand.ttf"))
    EMILIO_20 = FontProperties(fname=os.path.join(FONTS_DIR, "Emilio20.ttf"))
    BASEBALL_CLUB = FontProperties(fname=os.path.join(FONTS_DIR, "BaseballClub.otf"))
    BEACHDAY = FontProperties(fname=os.path.join(FONTS_DIR, "BeachDay.otf"))
    BUTTER_CHICKEN = FontProperties(fname=os.path.join(FONTS_DIR, "ButterChicken.ttf"))
    COLOR_SPORT = FontProperties(fname=os.path.join(FONTS_DIR, "ColorSport.ttf"))
    HANKY = FontProperties(fname=os.path.join(FONTS_DIR, "Hanky.otf"))
    LUCKIEST_GUY = FontProperties(fname=os.path.join(FONTS_DIR, "LuckiestGuy.ttf"))
    MILKY_WAY = FontProperties(fname=os.path.join(FONTS_DIR, "MilkyWay.ttf"))
    SAKANA = FontProperties(fname=os.path.join(FONTS_DIR, "Sakana.ttf"))
    SAUCE_TOMATO = FontProperties(fname=os.path.join(FONTS_DIR, "SauceTomato.otf"))
    SUNDAY_MAGIC = FontProperties(fname=os.path.join(FONTS_DIR, "SundayMagic.otf"))
    VALTY = FontProperties(fname=os.path.join(FONTS_DIR, "Valty.otf"))

    BOLTON = FontProperties(fname=os.path.join(FONTS_DIR, "Bolton.ttf"))
    CHASER = FontProperties(fname=os.path.join(FONTS_DIR, "Chaser.otf"))
    FUNGKY_BROW = FontProperties(fname=os.path.join(FONTS_DIR, "FungkyBrow.otf"))
    KURVACEOUS = FontProperties(fname=os.path.join(FONTS_DIR, "Kurvaceous.otf"))
    NATURE_KEYSTONE = FontProperties(fname=os.path.join(FONTS_DIR, "NatureKeystone.otf"))
    RACING_GAMES = FontProperties(fname=os.path.join(FONTS_DIR, "RacingGames.otf"))
    SS_DIAMOND = FontProperties(fname=os.path.join(FONTS_DIR, "ss-diamond.otf"))
    SS_MALIBU = FontProperties(fname=os.path.join(FONTS_DIR, "ss-malibu.otf"))
    VINTAGE_BROWNER = FontProperties(fname=os.path.join(FONTS_DIR, "VintageBrowner.otf"))
    VINTAGE_RUBICON = FontProperties(fname=os.path.join(FONTS_DIR, "VintageRubicon.otf"))
    VOEGIES = FontProperties(fname=os.path.join(FONTS_DIR, "Voegies.ttf"))

    @property
    def font_name(self) -> str:
        """Get the name of the FontProperties object."""
        return self.value.get_name()


ANNOTATION_FONT: Final = CustomFont.DEJA_VU_SANS_BOLD

TITLE_FONTS: Final = (
    CustomFont.LOBSTER,
    CustomFont.MONOTON,
    CustomFont.GOCHI_HAND,
    CustomFont.EMILIO_20,
    CustomFont.BASEBALL_CLUB,
    CustomFont.BEACHDAY,
    CustomFont.BUTTER_CHICKEN,
    CustomFont.COLOR_SPORT,
    CustomFont.HANKY,
    CustomFont.LUCKIEST_GUY,
    CustomFont.MILKY_WAY,
    CustomFont.SAKANA,
    CustomFont.SAUCE_TOMATO,
    CustomFont.SUNDAY_MAGIC,
    CustomFont.VALTY,
    CustomFont.BOLTON,
    CustomFont.FUNGKY_BROW,
    CustomFont.NATURE_KEYSTONE,
    CustomFont.RACING_GAMES,
    CustomFont.SS_DIAMOND,
    CustomFont.SS_MALIBU,
    CustomFont.VINTAGE_RUBICON,
    CustomFont.VOEGIES,
    CustomFont.MONTSERRAT_SEMIBOLD,
    CustomFont.INTER_SEMIBOLD,
    CustomFont.MANROPE_SEMIBOLD,
)

STATS_FONTS: Final = (
    CustomFont.LOBSTER,
    CustomFont.GOCHI_HAND,
    CustomFont.BASEBALL_CLUB,
    CustomFont.BEACHDAY,
    CustomFont.BUTTER_CHICKEN,
    CustomFont.LUCKIEST_GUY,
    CustomFont.SAKANA,
    CustomFont.SAUCE_TOMATO,
    CustomFont.SUNDAY_MAGIC,
    CustomFont.BOLTON,
    CustomFont.CHASER,
    CustomFont.KURVACEOUS,
    CustomFont.NATURE_KEYSTONE,
    CustomFont.RACING_GAMES,
    CustomFont.SS_DIAMOND,
    CustomFont.SS_MALIBU,
    CustomFont.VINTAGE_RUBICON,
    CustomFont.VOEGIES,
    CustomFont.MONTSERRAT_REGULAR,
    CustomFont.INTER_REGULAR,
    CustomFont.MANROPE_REGULAR,
)
