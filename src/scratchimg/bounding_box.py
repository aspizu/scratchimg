from __future__ import annotations

from msgspec import Struct


class BoundingBox(Struct):
    w: int
    h: int

    @classmethod
    def from_bbox(cls, bbox: tuple[int, int, int, int]) -> BoundingBox:
        return cls(w=bbox[2] - bbox[0], h=bbox[3] - bbox[1])

    def to_bbox(self, x: int, y: int) -> tuple[int, int, int, int]:
        return (x, y, x + self.w - 1, y + self.h - 1)

    def outset(self, size: int) -> BoundingBox:
        return BoundingBox(w=self.w + size * 2, h=self.h + size * 2)

    def outsetx(self, size: int) -> BoundingBox:
        return BoundingBox(w=self.w + size * 2, h=self.h)

    def outsety(self, size: int) -> BoundingBox:
        return BoundingBox(w=self.w, h=self.h + size * 2)

    def addx(self, size: int) -> BoundingBox:
        return BoundingBox(w=self.w + size, h=self.h)

    def addy(self, size: int) -> BoundingBox:
        return BoundingBox(w=self.w, h=self.h + size)

    def subx(self, size: int) -> BoundingBox:
        return BoundingBox(w=self.w - size, h=self.h)

    def suby(self, size: int) -> BoundingBox:
        return BoundingBox(w=self.w, h=self.h - size)

    def placex(self, other: BoundingBox) -> BoundingBox:
        return BoundingBox(w=self.w + other.w, h=max(self.h, other.h))

    def placey(self, other: BoundingBox) -> BoundingBox:
        return BoundingBox(w=max(self.w, other.w), h=self.h + other.h)
