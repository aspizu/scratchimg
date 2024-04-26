from __future__ import annotations

import PIL
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
from scratchimg import styles
from scratchimg.blocks import Block, Boolean, C, Literal, Menu, Reporter, Stack
from scratchimg.context import Context


def main() -> None:
    background = (211, 211, 211)
    padding = 10
    image = PIL.Image.new("RGB", (800, 600), background)
    ctx = Context(PIL.ImageDraw.Draw(image))
    ctx.draw.font = PIL.ImageFont.load("fonts/cherry-10-r.pil")
    stack = Stack(
        [
            Block(
                styles["motion"],
                ["move", Literal("10"), "steps"],
            ),
            Block(
                styles["looks"],
                ["say", Literal("Hello!"), "for", Literal("2"), "seconds"],
            ),
            Block(
                styles["sound"],
                ["clear sound effects"],
            ),
            Block(
                styles["events"],
                ["broadcast", Menu("message1")],
            ),
            Block(
                styles["control"],
                ["wait", Literal("1"), "seconds"],
            ),
            Block(
                styles["sensing"],
                ["ask", Literal("What's your name?"), "and wait"],
            ),
            Block(
                styles["variables"],
                [
                    "set",
                    Literal("my variable"),
                    "to",
                    Boolean(
                        styles["operators"],
                        [Literal("10"), "<", Literal("20")],
                    ),
                ],
            ),
            Block(
                styles["lists"],
                ["add", Literal("thing"), "to", Menu("my list")],
            ),
            Block(
                styles["custom"],
                [
                    "custom block",
                    Reporter(
                        styles["sensing"],
                        ["mouse x"],
                    ),
                ],
            ),
            C(
                styles["control"],
                [
                    "if",
                    Boolean(styles["operators"], [Literal("A"), "=", Literal("a")]),
                    "then",
                ],
                Stack([]),
            ),
        ]
    )
    c = C(
        styles["control"],
        ["if", Boolean(styles["operators"], [Literal("A"), "=", Literal("a")]), "then"],
        stack,
    )
    c.render(ctx, padding, padding)
    bounding_box = c.bounding_box(ctx).outset(padding)
    image = image.crop(bounding_box.to_bbox(0, 0))
    image.save("examples/example.png")


main()
