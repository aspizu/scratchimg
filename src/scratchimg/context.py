from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from msgspec import Struct, field

from .bounding_box import BoundingBox
from .style import Style

if TYPE_CHECKING:
    from PIL.ImageDraw import ImageDraw

    from .misc import Color


class Context(Struct):
    draw: ImageDraw
    style: Style = field(default_factory=Style)

    def outline(self, color: Color, verts: Sequence[tuple[int, int]]) -> None:
        iterator = iter(verts)
        for previous_vert in iterator:
            for next_vert in iterator:
                self.draw.line((previous_vert, next_vert), fill=color)
                previous_vert = next_vert

    def text_bounding_box(self, text: str) -> BoundingBox:
        return BoundingBox.from_bbox(self.draw.textbbox((0, 0), text))
