from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from msgspec import Struct

from .bounding_box import BoundingBox

if TYPE_CHECKING:
    from .context import Context
    from .style import BlockStyle

type Color = str | tuple[int, int, int] | None


class Literal(Struct):
    value: str

    def render(self, ctx: Context, x: int, y: int, style: BlockStyle) -> None:
        box = self.bounding_box(ctx)
        render_rounded_rectangle(
            ctx,
            box.to_bbox(x, y),
            roundness=ctx.style.literal_roundness,
            fill=ctx.style.literal_background,
            outline=style.outline,
        )
        ctx.draw.text(
            (x + ctx.style.padding_x, y + ctx.style.padding_y),
            self.value,
            fill=ctx.style.literal_foreground,
        )

    # Don't care about memory leaks, this is not a long-running program
    # @lru_cache
    def bounding_box(self, ctx: Context) -> BoundingBox:
        box = ctx.text_bounding_box(self.value)
        return box.outsetx(ctx.style.padding_x).outsety(ctx.style.padding_y)


class Menu(Struct):
    value: str

    def render(self, ctx: Context, x: int, y: int, style: BlockStyle) -> None:
        box = self.bounding_box(ctx)
        render_rounded_rectangle(
            ctx,
            box.to_bbox(x, y),
            roundness=ctx.style.literal_roundness,
            fill=style.menu_background,
            outline=style.outline,
        )
        ctx.draw.text(
            (x + ctx.style.padding_x, y + ctx.style.padding_y),
            self.value,
            fill=style.foreground,
        )

    # Don't care about memory leaks, this is not a long-running program
    # @lru_cache
    def bounding_box(self, ctx: Context) -> BoundingBox:
        box = ctx.text_bounding_box(self.value)
        return box.outsetx(ctx.style.padding_x).outsety(ctx.style.padding_y)


type BoxItem = str | Literal | Menu | Reporter | Boolean


class Box(Struct):
    items: Sequence[BoxItem]
    style: BlockStyle
    gap: int = 0
    min_height: int = 0

    def render(self, ctx: Context, x: int, y: int) -> None:
        box = self.bounding_box(ctx)
        for item in self.items:
            if isinstance(item, str):
                item_box = ctx.text_bounding_box(item)
                dy = (box.h - item_box.h) // 2
                ctx.draw.text((x, dy + y), item, fill=self.style.foreground)
            else:
                item_box = item.bounding_box(ctx)
                dy = (box.h - item_box.h) // 2
                if isinstance(item, Literal | Menu):
                    item.render(ctx, x, y + dy, self.style)
                else:
                    item.render(ctx, x, y + dy)
            x += item_box.w + self.gap

    def bounding_box(self, ctx: Context) -> BoundingBox:
        box = BoundingBox(0, self.min_height)
        for item in self.items:
            if isinstance(item, str):
                item_box = ctx.text_bounding_box(item)
            else:
                item_box = item.bounding_box(ctx)
            box = box.placex(item_box)
        return box.addx(ctx.style.gap * (len(self.items) - 1))


class Block(Struct):
    style: BlockStyle
    items: Sequence[BoxItem]
    is_last: bool = False

    def render(self, ctx: Context, x: int, y: int) -> None:
        box = Box(
            self.items,
            self.style,
            gap=ctx.style.gap,
            min_height=ctx.style.min_block_height,
        )
        render_block(
            ctx,
            box.bounding_box(ctx)
            .outsetx(ctx.style.padding_x)
            .outsety(ctx.style.padding_y)
            .to_bbox(x, y),
            self.style,
            self.is_last,
        )
        box.render(ctx, x + ctx.style.padding_x, y + ctx.style.padding_y)

    def bounding_box(self, ctx: Context) -> BoundingBox:
        box = Box(
            self.items,
            self.style,
            gap=ctx.style.gap,
            min_height=ctx.style.min_block_height,
        ).bounding_box(ctx)
        box = box.outsetx(ctx.style.padding_x).outsety(ctx.style.padding_y)
        if not self.is_last:
            box = box.addy(ctx.style.tab_height)
        return box


class Reporter(Struct):
    style: BlockStyle
    items: Sequence[BoxItem]

    def render(self, ctx: Context, x: int, y: int) -> None:
        box = Box(self.items, self.style, gap=ctx.style.gap)
        render_rounded_rectangle(
            ctx,
            box.bounding_box(ctx)
            .outsetx(ctx.style.padding_x)
            .outsety(ctx.style.padding_y)
            .to_bbox(x, y),
            roundness=ctx.style.reporter_roundness,
            fill=self.style.background,
            outline=self.style.outline,
            highlight=self.style.highlight,
            shadow=self.style.shadow,
        )
        box.render(ctx, x + ctx.style.padding_x, y + ctx.style.padding_y)

    def bounding_box(self, ctx: Context) -> BoundingBox:
        box = Box(self.items, self.style, gap=ctx.style.gap).bounding_box(ctx)
        return box.outsetx(ctx.style.padding_x).outsety(ctx.style.padding_y)


class Boolean(Struct):
    style: BlockStyle
    items: Sequence[BoxItem]

    def render(self, ctx: Context, x: int, y: int) -> None:
        box = Box(
            self.items,
            self.style,
            gap=ctx.style.gap,
        )
        bounding_box = box.bounding_box(ctx).outsety(ctx.style.padding_y)
        padding_x = (bounding_box.h // 2) - ctx.style.boolean_roundness
        render_rounded_rectangle(
            ctx,
            bounding_box.outsetx(padding_x).to_bbox(x, y),
            roundness=padding_x,
            fill=self.style.background,
            outline=self.style.outline,
            highlight=self.style.highlight,
            shadow=self.style.shadow,
        )
        box.render(ctx, x + padding_x, y + ctx.style.padding_y)

    def bounding_box(self, ctx: Context) -> BoundingBox:
        box = Box(
            self.items,
            self.style,
            gap=ctx.style.gap,
        )
        box = box.bounding_box(ctx).outsety(ctx.style.padding_y)
        padding_x = (box.h // 2) - ctx.style.boolean_roundness
        return box.outsetx(padding_x)


class Stack(Struct):
    items: Sequence[Block | C]

    def is_last(self) -> bool:
        return len(self.items) > 0 and self.items[-1].is_last

    def render(self, ctx: Context, x: int, y: int) -> None:
        for item in self.items:
            item_box = item.bounding_box(ctx)
            item.render(ctx, x, y)
            y += item_box.h - ctx.style.tab_height - 1

    def bounding_box(self, ctx: Context) -> BoundingBox:
        box = BoundingBox(0, 0)
        for item in self.items:
            item_box = item.bounding_box(ctx).suby(ctx.style.tab_height + 1)
            box = box.placey(item_box)
        if len(self.items) > 0 and not self.items[-1].is_last:
            box = box.addy(ctx.style.tab_height + 1)
        return box


class C(Struct):
    style: BlockStyle
    items: Sequence[BoxItem]
    stack: Stack
    is_last: bool = False

    def render(self, ctx: Context, x: int, y: int) -> None:
        box = Box(self.items, self.style, ctx.style.gap, ctx.style.min_block_height)
        items_bounding_box = box.bounding_box(ctx)
        stack_bounding_box = self.stack.bounding_box(ctx)
        is_stack_last = self.stack.is_last()
        height = max(stack_bounding_box.h, ctx.style.c_min_height)
        if not is_stack_last:
            height -= ctx.style.tab_height + 1
        render_c(
            ctx,
            self.style,
            x,
            y,
            x + ctx.style.padding_x * 2 + items_bounding_box.w - 1,
            y + ctx.style.padding_y * 2 + items_bounding_box.h - 1,
            height,
            is_stack_last=is_stack_last,
            is_last=self.is_last,
        )
        y += ctx.style.padding_y
        box.render(ctx, x + ctx.style.padding_x, y)
        x += ctx.style.c_width
        y += items_bounding_box.h + ctx.style.padding_y - 1
        self.stack.render(ctx, x, y)

    def bounding_box(self, ctx: Context) -> BoundingBox:
        box = Box(self.items, self.style, ctx.style.gap, ctx.style.min_block_height)
        box = box.bounding_box(ctx)
        stack_bounding_box = (
            self.stack.bounding_box(ctx)
            .addx(ctx.style.c_width)
            .placey(BoundingBox(0, ctx.style.c_min_height))
        )
        box = box.outsetx(ctx.style.padding_x).outsety(ctx.style.padding_y)
        box = box.placey(stack_bounding_box)
        if not self.stack.is_last():
            box = box.suby(ctx.style.tab_height + 1)
        box = box.addy(ctx.style.c_width)
        if not self.is_last:
            box = box.addy(ctx.style.tab_height)
        return box


def render_rounded_rectangle(
    ctx: Context,
    box: tuple[int, int, int, int],
    roundness: int,
    fill: Color = None,
    outline: Color = None,
    highlight: Color = None,
    shadow: Color = None,
) -> None:
    x0, y0, x1, y1 = box

    ctx.draw.polygon(
        (
            (x0 + roundness, y0),
            (x1 - roundness, y0),
            (x1, y0 + roundness),
            (x1, y1 - roundness),
            (x1 - roundness, y1),
            (x0 + roundness, y1),
            (x0, y1 - roundness),
            (x0, y0 + roundness),
        ),
        fill=fill,
        outline=outline,
    )

    if highlight:
        # fmt: off
        verts = [
            (x0 + 1, y0 + roundness),
            (x0 + roundness, y0 + 1),
            (x1 - roundness, y0 + 1),
            (x1 - 1, y0 + roundness),
        ]
        # fmt: on
        ctx.outline(highlight, verts)

    if shadow:
        # fmt: off
        verts = [
            (x0 + 1, y1 - roundness),
            (x0 + roundness, y1 - 1),
            (x1 - roundness, y1 - 1),
            (x1 - 1, y1 - roundness),
        ]
        # fmt: on
        ctx.outline(shadow, verts)


def render_block(
    ctx: Context,
    box: tuple[int, int, int, int],
    style: BlockStyle,
    is_last: bool,
) -> None:
    x0, y0, x1, y1 = box
    roundness = ctx.style.block_roundness
    tab_padding = ctx.style.tab_padding
    tab_width = ctx.style.tab_width
    tab_height = ctx.style.tab_height

    verts = [
        (x0 + roundness, y0),
        (x0 + roundness + tab_padding, y0),
        (x0 + roundness + tab_padding + tab_height, y0 + tab_height),
        (x0 + roundness + tab_padding + tab_height + tab_width, y0 + tab_height),
        (x0 + roundness + tab_padding + tab_height + tab_width + tab_height, y0),
        (x1 - roundness, y0),
        (x1, y0 + roundness),
        (x1, y1 - roundness),
        (x1 - roundness, y1),
    ]

    if not is_last:
        verts.extend(
            [
                (
                    x0 + roundness + tab_padding + tab_height + tab_width + tab_height,
                    y1,
                ),
                (
                    x0 + roundness + tab_padding + tab_height + tab_width,
                    y1 + tab_height,
                ),
                (x0 + roundness + tab_padding + tab_height, y1 + tab_height),
                (x0 + roundness + tab_padding, y1),
            ]
        )

    verts.extend(
        [
            (x0 + roundness, y1),
            (x0, y1 - roundness),
            (x0, y0 + roundness),
        ]
    )

    ctx.draw.polygon(verts, fill=style.background, outline=style.outline)

    if style.highlight:
        # fmt: off
        verts = [
            (x0 + 1, y0 + roundness),
            (x0 + roundness, y0 + 1),
            (x0 + roundness + tab_padding, y0 + 1),
            (x0 + roundness + tab_padding + tab_height, y0 + 1 + tab_height),
            (x0 + roundness + tab_padding + tab_height + tab_width, y0 + 1 + tab_height),
            (x0 + roundness + tab_padding + tab_height + tab_width + tab_height, y0 + 1),
            (x1 - roundness, y0 + 1),
            (x1 - 1, y0 + roundness),
        ]
        # fmt: on
        ctx.outline(style.highlight, verts)

    if style.shadow:
        # fmt: off
        verts = [
            (x0 + 1, y1 - roundness),
            (x0 + roundness, y1 - 1),
            (x0 + roundness + tab_padding, y1 - 1),
            (x0 + roundness + tab_padding + tab_height, y1 - 1 + tab_height),
            (x0 + roundness + tab_padding + tab_height + tab_width, y1 - 1 + tab_height),
            (x0 + roundness + tab_padding + tab_height + tab_width + tab_height, y1 - 1),
            (x1 - roundness, y1 - 1),
            (x1 - 1, y1 - roundness),
        ]
        # fmt: on
        ctx.outline(style.shadow, verts)


def render_c(
    ctx: Context,
    style: BlockStyle,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    height: int,
    is_stack_last: bool,
    is_last: bool,
) -> None:
    width = ctx.style.c_width
    roundness = ctx.style.c_roundness
    tab_padding = ctx.style.tab_padding
    tab_width = ctx.style.tab_width
    tab_height = ctx.style.tab_height

    verts = [
        (x0 + roundness, y0),
        (x0 + roundness + tab_padding, y0),
        (x0 + roundness + tab_padding + tab_height, y0 + tab_height),
        (x0 + roundness + tab_padding + tab_height + tab_width, y0 + tab_height),
        (x0 + roundness + tab_padding + tab_height + tab_width + tab_height, y0),
        (x1 - roundness, y0),
        (x1, y0 + roundness),
        (x1, y1 - roundness),
        (x1 - roundness, y1),
        (
            x0 + width + roundness + tab_padding + tab_height + tab_width + tab_height,
            y1,
        ),
        (
            x0 + width + roundness + tab_padding + tab_height + tab_width,
            y1 + tab_height,
        ),
        (x0 + width + roundness + tab_padding + tab_height, y1 + tab_height),
        (x0 + width + roundness + tab_padding, y1),
        (x0 + width + roundness, y1),
        (x0 + width, y1 + roundness),
        (x0 + width, y1 + height - roundness),
        (x0 + width + roundness, y1 + height),
        *(
            [
                (x0 + width + roundness + tab_padding, y1 + height),
                (
                    x0 + width + roundness + tab_padding + tab_height,
                    y1 + height + tab_height,
                ),
                (
                    x0 + width + roundness + tab_padding + tab_height + tab_width,
                    y1 + height + tab_height,
                ),
                (
                    x0
                    + width
                    + roundness
                    + tab_padding
                    + tab_height
                    + tab_width
                    + tab_height,
                    y1 + height,
                ),
            ]
            if not is_stack_last
            else []
        ),
        (x1 - roundness, y1 + height),
        (x1, y1 + height + roundness),
        (x1, y1 + height + width - roundness),
        (x1 - roundness, y1 + height + width),
        *(
            [
                (
                    x0 + roundness + tab_padding + tab_height + tab_width + tab_height,
                    y1 + height + width,
                ),
                (
                    x0 + roundness + tab_padding + tab_height + tab_width,
                    y1 + tab_height + height + width,
                ),
                (
                    x0 + roundness + tab_padding + tab_height,
                    y1 + tab_height + height + width,
                ),
                (x0 + roundness + tab_padding, y1 + height + width),
            ]
            if not is_last
            else []
        ),
        (x0 + roundness, y1 + height + width),
        (x0, y1 + height + width - roundness),
        (x0, y0 + roundness),
    ]

    ctx.draw.polygon(verts, fill=style.background, outline=style.outline)

    if style.highlight:
        verts = [
            (x0 + 1, y0 + roundness),
            (x0 + roundness, y0 + 1),
            (x0 + roundness + tab_padding, y0 + 1),
            (x0 + roundness + tab_padding + tab_height, y0 + 1 + tab_height),
            (
                x0 + roundness + tab_padding + tab_height + tab_width,
                y0 + 1 + tab_height,
            ),
            (
                x0 + roundness + tab_padding + tab_height + tab_width + tab_height,
                y0 + 1,
            ),
            (x1 - roundness, y0 + 1),
            (x1 - 1, y0 + roundness),
        ]

        ctx.outline(style.highlight, verts)

        # top highlight of bottom section
        verts = [
            (x0 + width, y1 + height - roundness + 1),
            (x0 + width + roundness, y1 + height + 1),
            *(
                [
                    (x0 + width + roundness + tab_padding, y1 + height + 1),
                    (
                        x0 + width + roundness + tab_padding + tab_height,
                        y1 + height + 1 + tab_height,
                    ),
                    (
                        x0 + width + roundness + tab_padding + tab_height + tab_width,
                        y1 + height + 1 + tab_height,
                    ),
                    (
                        x0
                        + width
                        + roundness
                        + tab_padding
                        + tab_height
                        + tab_width
                        + tab_height,
                        y1 + height + 1,
                    ),
                ]
                if not is_stack_last
                else []
            ),
            (x1 - roundness, y1 + height + 1),
            (x1 - 1, y1 + height + roundness),
        ]

        ctx.outline(style.highlight, verts)

    if style.shadow:
        verts = [
            (x0 + 1, y1 + height + width - roundness),
            (x0 + roundness, y1 + height + width - 1),
            *(
                [
                    (x0 + roundness + tab_padding, y1 + height + width - 1),
                    (
                        x0 + roundness + tab_padding + tab_height,
                        y1 + height + width - 1 + tab_height,
                    ),
                    (
                        x0 + roundness + tab_padding + tab_height + tab_width,
                        y1 + height + width - 1 + tab_height,
                    ),
                    (
                        x0
                        + roundness
                        + tab_padding
                        + tab_height
                        + tab_width
                        + tab_height,
                        y1 + height + width - 1,
                    ),
                ]
                if not is_last
                else []
            ),
            (x1 - roundness, y1 + height + width - 1),
            (x1 - 1, y1 + height + width - roundness),
        ]

        ctx.outline(style.shadow, verts)

        # bottom shadow of top section

        verts = [
            (x0 + width, y1 + roundness - 1),
            (x0 + width + roundness, y1 - 1),
            (x0 + width + roundness + tab_padding, y1 - 1),
            (x0 + width + roundness + tab_padding + tab_height, y1 - 1 + tab_height),
            (
                x0 + width + roundness + tab_padding + tab_height + tab_width,
                y1 - 1 + tab_height,
            ),
            (
                x0
                + width
                + roundness
                + tab_padding
                + tab_height
                + tab_width
                + tab_height,
                y1 - 1,
            ),
            (x1 - roundness, y1 - 1),
            (x1 - 1, y1 - roundness),
        ]

        ctx.outline(style.shadow, verts)
