"""128x128 indexed texture builder for picoCAD 2.

picoCAD textures are exactly 128x128 pixels. Each pixel stores one of 16
palette indices (0..15) which serialise as a single hex digit ('0'..'f'),
so the whole texture becomes a 16384-character hex string in the model
file, row-major, top-to-bottom.

Recipes typically work in "tiles": square UV rectangles that each map to
one face. :class:`Texture` exposes :meth:`paint_tile` to flood-fill a
rectangle with one palette index, which is enough for blocky low-poly
art. For finer control, use :meth:`set_pixel` directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

__all__ = ["SIZE", "N", "Texture", "Tile"]

#: Pixels per side of the texture image.
SIZE: int = 128

#: Total pixel count (``SIZE * SIZE`` = 16384).
N: int = SIZE * SIZE

#: A UV rectangle ``(u0, v0, u1, v1)`` with all values in ``[0.0, 1.0]``.
type Tile = tuple[float, float, float, float]


class Texture:
    """A 128x128 indexed-pixel image, serialisable to picoCAD's hex string.

    Parameters
    ----------
    background_color
        Palette index (0..15) to pre-fill every pixel with. Defaults to 1
        (white in the default palette), matching picoCAD's new-file look.

    Attributes
    ----------
    pixels : list[int]
        Flat row-major list of palette indices, length :data:`N`. Mutate
        via :meth:`set_pixel`, :meth:`paint_tile`, or :meth:`fill`.
    """

    pixels: list[int]

    def __init__(self, background_color: int = 1) -> None:
        self.pixels = [background_color] * N

    def fill(self, color: int) -> None:
        """Overwrite every pixel with ``color``."""
        self.pixels = [color] * N

    def paint_tile(self, tile: Tile, color: int) -> None:
        """Flood-fill the pixel rectangle covered by UV ``tile``.

        The tile is a ``(u0, v0, u1, v1)`` rectangle in UV space ``[0, 1]``.
        ``[0, 0]`` is the top-left of the texture image, matching picoCAD.

        Coordinates are clipped to the texture bounds, so partially
        off-screen tiles are safe.
        """
        u0, v0, u1, v1 = tile
        x0 = max(0, int(u0 * SIZE))
        x1 = min(SIZE, int(u1 * SIZE))
        y0 = max(0, int(v0 * SIZE))
        y1 = min(SIZE, int(v1 * SIZE))
        for y in range(y0, y1):
            base = y * SIZE
            for x in range(x0, x1):
                self.pixels[base + x] = color

    def set_pixel(self, x: int, y: int, color: int) -> None:
        """Set a single pixel. Out-of-bounds coordinates are ignored."""
        if 0 <= x < SIZE and 0 <= y < SIZE:
            self.pixels[y * SIZE + x] = color

    def paint_pixels(self, coords: Iterable[tuple[int, int]], color: int) -> None:
        """Set many pixels at once. Convenient for non-rectangular art."""
        for x, y in coords:
            self.set_pixel(x, y, color)

    def to_hex(self) -> str:
        """Return the 16384-character hex string picoCAD stores as ``pixels``.

        Raises
        ------
        ValueError
            If the pixel buffer's length is not :data:`N`, or any index
            overflows a hex digit (i.e. ``not 0 <= c <= 15``).
        """
        if len(self.pixels) != N:
            raise ValueError(f"pixels must be {N} long, got {len(self.pixels)}")
        out = "".join(f"{c:x}" for c in self.pixels)
        if len(out) != N:
            raise ValueError(f"hex output must be {N} long, got {len(out)}")
        return out
