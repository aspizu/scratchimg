from __future__ import annotations

from typing import TYPE_CHECKING

from msgspec import Struct

if TYPE_CHECKING:
    from .misc import Color


class Style(Struct):
    min_block_height: int = 22
    padding_x: int = 6
    padding_y: int = 3
    gap: int = 4
    block_roundness: int = 2
    reporter_roundness: int = 2
    boolean_roundness: int = 2
    literal_roundness: int = 2
    c_roundness: int = 2
    c_width: int = 16
    c_min_height: int = 16
    tab_padding: int = 6
    tab_width: int = 8
    tab_height: int = 4

    literal_background: Color = "white"
    literal_foreground: Color = "black"


class BlockStyle(Struct):
    background: Color
    foreground: Color
    outline: Color
    highlight: Color
    shadow: Color
    menu_background: Color
