from __future__ import annotations

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

from .blocks import Block, Boolean, C, Literal, Menu, Reporter, Stack
from .context import Context
from .style import BlockStyle


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore


theme = """
CATEGORY   FOREGROUND  HIGHLIGHT   BACKGROUND  SHADOW      OUTLINE
motion     #a2beff     #5b84ff     #4a6cd4     #4160be     #304891
looks      #d7abff     #a868ff     #8a55d7     #7b4bc0     #5d3893
sound      #ff9bff     #e252ec     #bb42c3     #a73aae     #802a85
events     #ffd18c     #f29f3c     #c88330     #b3752a     #89581e
control    #fff17a     #ffcd22     #e1a91a     #c99716     #9a730e
sensing    #89edff     #37c8ff     #2ca5e2     #2693ca     #1b709b
operators  #b1fc73     #71dd18     #5cb712     #52a40f     #3d7d09
variables  #ffcc77     #ff981d     #ee7d16     #d56f12     #a3540b
lists      #ffaf80     #f76f2b     #cc5b22     #b7511d     #8c3c14
custom     #b68ae4     #7939ba     #632d99     #582789     #421c68
"""

styles = {}
for line in theme.split("\n"):
    line = line.strip()
    if line == "":
        continue
    if line.startswith("CATEGORY"):
        continue
    category, fg, hl, bg, sh, ol = line.split()
    styles[category] = BlockStyle(
        background=hex_to_rgb(bg),
        foreground=hex_to_rgb(fg),
        outline=hex_to_rgb(ol),
        highlight=hex_to_rgb(hl),
        shadow=hex_to_rgb(sh),
        menu_background=hex_to_rgb(sh),
    )


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
    image.save("output.png")
