"""Default 16-color palette and shading ramps for picoCAD 2.

picoCAD textures are limited to 16 colors, one of which is treated as
transparent. The defaults below are a neutral gray ramp plus a black /
white pair, with palette slot 14 reserved as the transparent color (so a
brand-new model renders fully opaque by default).

Recipes can override :data:`DEFAULT_COLORS`, :data:`DEFAULT_SHADE_PAL_1`,
and :data:`DEFAULT_SHADE_PAL_2` freely.
"""

from __future__ import annotations

__all__ = [
    "DEFAULT_BACKGROUND_COLOR",
    "DEFAULT_COLORS",
    "DEFAULT_SHADE_PAL_1",
    "DEFAULT_SHADE_PAL_2",
    "DEFAULT_TRANSPARENT_COLOR",
    "PALETTE_SIZE",
    "Color",
]

#: Number of palette entries picoCAD stores per model.
PALETTE_SIZE: int = 16

#: An ``(r, g, b)`` triple in ``[0.0, 1.0]``.
type Color = tuple[float, float, float]


#: Default 16-color palette. Slot 14 is reserved as the transparent color,
#: slot 1 is white (also the default background). Slots 2-5 form a gray
#: shading ramp for white; slots 0 and 5 cap black at both ends.
DEFAULT_COLORS: list[Color] = [
    (0.00, 0.00, 0.00),  # 0  black
    (1.00, 1.00, 1.00),  # 1  white
    (0.78, 0.78, 0.80),  # 2  light gray (white shaded step 1)
    (0.55, 0.55, 0.57),  # 3  mid gray (step 2)
    (0.30, 0.30, 0.32),  # 4  dark (step 3)
    (0.20, 0.20, 0.22),  # 5  darkest
    (0.65, 0.65, 0.67),  # 6
    (0.85, 0.85, 0.87),  # 7
    (0.60, 0.60, 0.62),  # 8
    (0.90, 0.90, 0.92),  # 9
    (0.95, 0.95, 0.95),  # 10
    (0.92, 0.92, 0.94),  # 11
    (0.50, 0.50, 0.52),  # 12
    (0.40, 0.40, 0.42),  # 13
    (1.00, 1.00, 1.00),  # 14 reserved (transparent_color by default)
    (0.97, 0.97, 0.99),  # 15
]

#: Lit row of the shading ramp. Identity by default: each color emits
#: itself when fully lit.
DEFAULT_SHADE_PAL_1: list[int] = list(range(PALETTE_SIZE))

#: Shaded row of the ramp. White (1) shades toward light gray (2), then
#: mid gray (3), then dark (4). Black stays black.
DEFAULT_SHADE_PAL_2: list[int] = [0, 2, 3, 4, 5, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

#: Palette index picoCAD treats as fully transparent. Slot 14 by default
#: (unused by :data:`DEFAULT_COLORS` recipes).
DEFAULT_TRANSPARENT_COLOR: int = 14

#: Palette index picoCAD paints behind everything else (drawn first).
#: White (slot 1) by default, matching picoCAD's own new-file template.
DEFAULT_BACKGROUND_COLOR: int = 1
