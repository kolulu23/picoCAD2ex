"""Recipe: low-poly football boot v2 for picoCAD 2.

A refined blue-and-white soccer cleat with a more boot-like silhouette,
three lateral stripes, actual lace strips, and a detailed 128x128 texture
(stitching, sole-plate grips, brand marks). This variant writes to a
separate file so the original ``football_shoe.txt`` is preserved.

Run::

    uv run python scripts/football_shoe/gen_football_shoe_kimi-k2.7-code.py

Outputs ``models/football_shoe/football_shoe_kimi-k2.7-code.txt``.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from picocad.model import Camera, Face, Mesh, Model, Node
from picocad.texture import Texture
from picocad.uv import ensure_outward, project_uv

if TYPE_CHECKING:
    from collections.abc import Sequence

Vec3 = tuple[float, float, float]

TILE = 0.125  # 16x16 px per tile on 128x128 texture (8x8 grid)


def _tile(row: int, col: int) -> tuple[float, float, float, float]:
    """Return UV tile rect for (row, col) in 8x8 grid, 0.125-sized."""
    u0 = col * TILE
    v0 = row * TILE
    return (u0, v0, u0 + TILE, v0 + TILE)


def _tile_span(row: int, col: int, w: int, h: int) -> tuple[float, float, float, float]:
    """Return a tile spanning ``w`` cols x ``h`` rows starting at (row,col)."""
    u0 = col * TILE
    v0 = row * TILE
    return (u0, v0, u0 + w * TILE, v0 + h * TILE)


def _flat(verts: Sequence[Vec3]) -> list[float]:
    """Flatten [(x,y,z), ...] into [x,y,z, x,y,z, ...]."""
    out: list[float] = []
    for v in verts:
        out.extend(v)
    return out


# ------------------------------------------------------------------- palette
# Blue + white football boot palette, 16 slots. Slot 14 = transparent.
BOOT_COLORS: list[Vec3] = [
    (0.00, 0.00, 0.00),  #  0 black (lace holes, outlines)
    (0.98, 0.98, 0.98),  #  1 white (sole, stripes, laces)
    (0.18, 0.42, 0.80),  #  2 royal blue (main upper)
    (0.08, 0.22, 0.52),  #  3 dark blue (shaded upper)
    (0.35, 0.58, 0.92),  #  4 light blue (lit upper)
    (0.03, 0.10, 0.28),  #  5 navy (liner, deep shadows)
    (0.78, 0.80, 0.84),  #  6 silver (sole plate, studs)
    (0.45, 0.48, 0.52),  #  7 dark silver (stud shadow)
    (0.90, 0.92, 0.94),  #  8 light silver (stud highlight)
    (0.62, 0.66, 0.70),  #  9 mid gray (sole detail)
    (0.28, 0.30, 0.33),  # 10 charcoal (grip lines)
    (0.12, 0.32, 0.65),  # 11 denim blue (toe cap)
    (0.04, 0.14, 0.38),  # 12 deep blue (heel counter)
    (0.94, 0.95, 0.96),  # 13 off-white
    (1.00, 1.00, 1.00),  # 14 transparent (reserved)
    (0.70, 0.82, 0.95),  # 15 pale sky highlight
]

BOOT_SHADE_PAL_1: list[int] = [
    0,  # 0 black
    13,  # 1 white -> off-white (lit already bright)
    4,  # 2 royal blue -> light blue
    2,  # 3 dark blue -> royal blue
    4,  # 4 light blue
    3,  # 5 navy -> dark blue
    8,  # 6 silver -> light silver
    6,  # 7 dark silver -> silver
    8,  # 8 light silver
    6,  # 9 mid gray -> silver
    7,  # 10 charcoal -> dark silver
    2,  # 11 denim -> royal blue
    3,  # 12 deep blue -> dark blue
    1,  # 13 off-white -> white
    14,  # 14 transparent
    4,  # 15 pale sky -> light blue
]

BOOT_SHADE_PAL_2: list[int] = [
    0,  # 0 black
    6,  # 1 white -> silver (shadow reads as ambient reflection)
    3,  # 2 royal blue -> dark blue
    5,  # 3 dark blue -> navy
    2,  # 4 light blue -> royal blue
    0,  # 5 navy -> black
    7,  # 6 silver -> dark silver
    10,  # 7 dark silver -> charcoal
    6,  # 8 light silver -> silver
    7,  # 9 mid gray -> dark silver
    0,  # 10 charcoal -> black
    3,  # 11 denim -> dark blue
    5,  # 12 deep blue -> navy
    9,  # 13 off-white -> mid gray
    14,  # 14 transparent
    3,  # 15 pale sky -> dark blue
]


# --------------------------------------------------------------------- parts


def _build_sole() -> Node:
    """Return the sole-plate node (bottom + sides, ready for studs)."""
    # Bottom ring (y = -0.55), top ring (y = -0.38). Slightly rounded toe.
    bottom: list[Vec3] = [
        (-1.05, -0.55, -0.20),  # 0 heel-left
        (-0.30, -0.56, -0.34),  # 1 mid-left
        (0.35, -0.54, -0.30),  # 2 fore-left
        (0.95, -0.50, -0.12),  # 3 toe-left
        (0.95, -0.50, 0.12),  # 4 toe-right
        (0.35, -0.54, 0.30),  # 5 fore-right
        (-0.30, -0.56, 0.34),  # 6 mid-right
        (-1.05, -0.55, 0.20),  # 7 heel-right
    ]
    top: list[Vec3] = [
        (-1.05, -0.38, -0.20),
        (-0.30, -0.38, -0.34),
        (0.35, -0.36, -0.30),
        (0.95, -0.34, -0.12),
        (0.95, -0.34, 0.12),
        (0.35, -0.36, 0.30),
        (-0.30, -0.38, 0.34),
        (-1.05, -0.38, 0.20),
    ]
    verts = bottom + top
    all_v = verts

    faces: list[Face] = []
    # Sole bottom as two quads (split at mid) for better affine mapping.
    faces.append(
        Face(
            vertex_ids=ensure_outward([0, 1, 2, 3, 4, 5, 6, 7], all_v),
            uvs=project_uv([0, 1, 2, 3, 4, 5, 6, 7], all_v, _tile_span(0, 0, 4, 2)),
            color=6,
        )
    )
    # Sole top
    faces.append(
        Face(
            vertex_ids=ensure_outward([8, 9, 10, 11, 12, 13, 14, 15], all_v),
            uvs=project_uv([8, 9, 10, 11, 12, 13, 14, 15], all_v, _tile_span(0, 0, 4, 2)),
            color=9,
        )
    )
    # Sides: left, right, heel (one face each around the ring)
    faces.append(
        Face(
            vertex_ids=ensure_outward([0, 8, 9, 1], all_v),
            uvs=project_uv([0, 8, 9, 1], all_v, _tile(0, 4)),
            color=10,
        )
    )
    faces.append(
        Face(
            vertex_ids=ensure_outward([1, 9, 10, 2], all_v),
            uvs=project_uv([1, 9, 10, 2], all_v, _tile(0, 5)),
            color=10,
        )
    )
    faces.append(
        Face(
            vertex_ids=ensure_outward([2, 10, 11, 3], all_v),
            uvs=project_uv([2, 10, 11, 3], all_v, _tile(0, 6)),
            color=10,
        )
    )
    faces.append(
        Face(
            vertex_ids=ensure_outward([3, 11, 12, 4], all_v),
            uvs=project_uv([3, 11, 12, 4], all_v, _tile(0, 7)),
            color=10,
        )
    )
    faces.append(
        Face(
            vertex_ids=ensure_outward([4, 12, 13, 5], all_v),
            uvs=project_uv([4, 12, 13, 5], all_v, _tile(1, 0)),
            color=10,
        )
    )
    faces.append(
        Face(
            vertex_ids=ensure_outward([5, 13, 14, 6], all_v),
            uvs=project_uv([5, 13, 14, 6], all_v, _tile(1, 1)),
            color=10,
        )
    )
    faces.append(
        Face(
            vertex_ids=ensure_outward([6, 14, 15, 7], all_v),
            uvs=project_uv([6, 14, 15, 7], all_v, _tile(1, 2)),
            color=10,
        )
    )
    faces.append(
        Face(
            vertex_ids=ensure_outward([7, 15, 8, 0], all_v),
            uvs=project_uv([7, 15, 8, 0], all_v, _tile(1, 3)),
            color=10,
        )
    )

    mesh = Mesh(name="sole", vertices=_flat(verts), faces=faces)
    return Node(name="sole", mesh=mesh)


def _build_upper() -> Node:
    """Return the upper boot body node."""
    # Bottom ring sits on sole top (y=-0.38).
    btm: list[Vec3] = [
        (-1.05, -0.38, -0.20),  # 0 heel-left
        (-0.30, -0.38, -0.34),  # 1 mid-left
        (0.35, -0.36, -0.30),  # 2 fore-left
        (0.95, -0.34, -0.12),  # 3 toe-left
        (0.95, -0.34, 0.12),  # 4 toe-right
        (0.35, -0.36, 0.30),  # 5 fore-right
        (-0.30, -0.38, 0.34),  # 6 mid-right
        (-1.05, -0.38, 0.20),  # 7 heel-right
    ]
    # Mid ring (y ~ 0.0).
    mid: list[Vec3] = [
        (-1.05, 0.0, -0.18),
        (-0.35, 0.0, -0.30),
        (0.30, 0.02, -0.26),
        (0.90, 0.04, -0.10),
        (0.90, 0.04, 0.10),
        (0.30, 0.02, 0.26),
        (-0.35, 0.0, 0.30),
        (-1.05, 0.0, 0.18),
    ]
    # Collar ring (y ~ 0.18).
    collar: list[Vec3] = [
        (-1.05, 0.18, -0.15),
        (-0.45, 0.12, -0.26),
        (0.15, 0.14, -0.22),
        (0.55, 0.16, -0.08),
        (0.55, 0.16, 0.08),
        (0.15, 0.14, 0.22),
        (-0.45, 0.12, 0.26),
        (-1.05, 0.18, 0.15),
    ]
    # Toe cap tip (raised).
    toe_tip: Vec3 = (1.12, -0.22, 0.0)

    verts = btm + mid + collar + [toe_tip]
    all_v = verts

    faces: list[Face] = []
    # Left wall: btm->mid and mid->collar quads for first 4 sections.
    for i in range(4):
        j = (i + 1) % 8
        faces.append(
            Face(
                vertex_ids=ensure_outward([i, j, j + 8, i + 8], all_v),
                uvs=project_uv([i, j, j + 8, i + 8], all_v, _tile_span(2, 0, 2, 1)),
                color=2,
            )
        )
        faces.append(
            Face(
                vertex_ids=ensure_outward([i + 8, j + 8, j + 16, i + 16], all_v),
                uvs=project_uv([i + 8, j + 8, j + 16, i + 16], all_v, _tile_span(2, 2, 2, 1)),
                color=2,
            )
        )
    # Right wall: slightly darker for contrast.
    for i in range(4, 8):
        j = (i + 1) % 8
        faces.append(
            Face(
                vertex_ids=ensure_outward([i, j, j + 8, i + 8], all_v),
                uvs=project_uv([i, j, j + 8, i + 8], all_v, _tile_span(2, 4, 2, 1)),
                color=3,
            )
        )
        faces.append(
            Face(
                vertex_ids=ensure_outward([i + 8, j + 8, j + 16, i + 16], all_v),
                uvs=project_uv([i + 8, j + 8, j + 16, i + 16], all_v, _tile_span(2, 6, 2, 1)),
                color=3,
            )
        )

    # Heel back face (between right/left walls).
    faces.append(
        Face(
            vertex_ids=ensure_outward([7, 0, 8, 15], all_v),
            uvs=project_uv([7, 0, 8, 15], all_v, _tile(4, 0)),
            color=12,
        )
    )
    faces.append(
        Face(
            vertex_ids=ensure_outward([15, 8, 16, 23], all_v),
            uvs=project_uv([15, 8, 16, 23], all_v, _tile(4, 1)),
            color=12,
        )
    )

    # Toe cap (pentagon).
    faces.append(
        Face(
            vertex_ids=ensure_outward([2, 3, 4, 5, 24], all_v),
            uvs=project_uv([2, 3, 4, 5, 24], all_v, _tile_span(4, 2, 1, 2)),
            color=11,
        )
    )

    # Instep / lace deck: white panels on top.
    # Left instep: collar -> mid sections 1-3.
    faces.append(
        Face(
            vertex_ids=ensure_outward([16, 17, 9, 8], all_v),
            uvs=project_uv([16, 17, 9, 8], all_v, _tile_span(4, 3, 1, 2)),
            color=1,
        )
    )
    faces.append(
        Face(
            vertex_ids=ensure_outward([17, 18, 10, 9], all_v),
            uvs=project_uv([17, 18, 10, 9], all_v, _tile_span(4, 4, 1, 2)),
            color=1,
        )
    )
    faces.append(
        Face(
            vertex_ids=ensure_outward([18, 19, 11, 10], all_v),
            uvs=project_uv([18, 19, 11, 10], all_v, _tile_span(4, 5, 1, 2)),
            color=1,
        )
    )
    # Right instep.
    faces.append(
        Face(
            vertex_ids=ensure_outward([20, 21, 13, 12], all_v),
            uvs=project_uv([20, 21, 13, 12], all_v, _tile_span(5, 0, 1, 2)),
            color=1,
        )
    )
    faces.append(
        Face(
            vertex_ids=ensure_outward([21, 22, 14, 13], all_v),
            uvs=project_uv([21, 22, 14, 13], all_v, _tile_span(5, 1, 1, 2)),
            color=1,
        )
    )
    faces.append(
        Face(
            vertex_ids=ensure_outward([22, 23, 15, 14], all_v),
            uvs=project_uv([22, 23, 15, 14], all_v, _tile_span(5, 2, 1, 2)),
            color=1,
        )
    )

    # Collar rim (double-sided so the opening reads from both sides).
    faces.append(
        Face(
            vertex_ids=ensure_outward([16, 23, 22, 21, 20, 19, 18, 17], all_v),
            uvs=project_uv([16, 23, 22, 21, 20, 19, 18, 17], all_v, _tile(5, 3)),
            color=5,
            dbl=True,
        )
    )

    mesh = Mesh(name="upper", vertices=_flat(verts), faces=faces)
    return Node(name="upper", mesh=mesh)


def _build_heel_counter() -> Node:
    """Return a raised heel-counter shell."""
    verts: list[Vec3] = [
        (-1.05, 0.18, -0.15),  # 0
        (-0.85, 0.12, -0.22),  # 1
        (-0.85, 0.12, 0.22),  # 2
        (-1.05, 0.18, 0.15),  # 3
        (-1.05, 0.40, -0.12),  # 4
        (-0.85, 0.32, -0.18),  # 5
        (-0.85, 0.32, 0.18),  # 6
        (-1.05, 0.40, 0.12),  # 7
    ]
    all_v = verts
    faces: list[Face] = [
        Face(
            vertex_ids=ensure_outward([0, 1, 5, 4], all_v),
            uvs=project_uv([0, 1, 5, 4], all_v, _tile(5, 4)),
            color=12,
        ),
        Face(
            vertex_ids=ensure_outward([2, 3, 7, 6], all_v),
            uvs=project_uv([2, 3, 7, 6], all_v, _tile(5, 5)),
            color=12,
        ),
        Face(
            vertex_ids=ensure_outward([3, 0, 4, 7], all_v),
            uvs=project_uv([3, 0, 4, 7], all_v, _tile(5, 6)),
            color=12,
        ),
        Face(
            vertex_ids=ensure_outward([1, 2, 6, 5], all_v),
            uvs=project_uv([1, 2, 6, 5], all_v, _tile(5, 7)),
            color=12,
            dbl=True,
        ),
        Face(
            vertex_ids=ensure_outward([4, 5, 6, 7], all_v),
            uvs=project_uv([4, 5, 6, 7], all_v, _tile(6, 0)),
            color=12,
        ),
    ]
    mesh = Mesh(name="heel_counter", vertices=_flat(verts), faces=faces)
    return Node(name="heel_counter", mesh=mesh)


def _build_studs() -> Node:
    """Return a folder of 8 conical studs."""
    positions: list[Vec3] = [
        (0.70, -0.55, -0.16),
        (0.70, -0.55, 0.16),
        (0.25, -0.56, -0.22),
        (0.25, -0.56, 0.22),
        (-0.55, -0.55, -0.14),
        (-0.55, -0.55, 0.14),
        (-0.90, -0.55, -0.12),
        (-0.90, -0.55, 0.12),
    ]
    stud_nodes: list[Node] = []
    for idx, base in enumerate(positions):
        bx, by, bz = base
        r = 0.055
        h = 0.09
        cv: list[Vec3] = [
            (bx - r, by, bz - r),
            (bx + r, by, bz - r),
            (bx + r, by, bz + r),
            (bx - r, by, bz + r),
            (bx, by - h, bz),
        ]
        all_cv = cv
        cf: list[Face] = [
            Face(
                vertex_ids=ensure_outward([0, 1, 4], all_cv),
                uvs=project_uv([0, 1, 4], all_cv, _tile(6, 1 + (idx % 4))),
                color=7,
            ),
            Face(
                vertex_ids=ensure_outward([1, 2, 4], all_cv),
                uvs=project_uv([1, 2, 4], all_cv, _tile(6, 1 + ((idx + 1) % 4))),
                color=8,
            ),
            Face(
                vertex_ids=ensure_outward([2, 3, 4], all_cv),
                uvs=project_uv([2, 3, 4], all_cv, _tile(6, 1 + ((idx + 2) % 4))),
                color=8,
            ),
            Face(
                vertex_ids=ensure_outward([3, 0, 4], all_cv),
                uvs=project_uv([3, 0, 4], all_cv, _tile(6, 1 + ((idx + 3) % 4))),
                color=7,
            ),
        ]
        stud_nodes.append(
            Node(name=f"stud_{idx}", mesh=Mesh(name=f"stud_{idx}", vertices=_flat(cv), faces=cf))
        )
    return Node(name="studs", children=stud_nodes)


def _build_tongue() -> Node:
    """Return the tongue flap node."""
    verts: list[Vec3] = [
        (0.15, 0.14, -0.18),  # 0 base-left
        (0.15, 0.14, 0.18),  # 1 base-right
        (0.55, 0.30, -0.10),  # 2 tip-left
        (0.55, 0.30, 0.10),  # 3 tip-right
    ]
    all_v = verts
    faces: list[Face] = [
        Face(
            vertex_ids=ensure_outward([0, 1, 3, 2], all_v),
            uvs=project_uv([0, 1, 3, 2], all_v, _tile_span(6, 5, 1, 2)),
            color=1,
            dbl=True,
        )
    ]
    return Node(name="tongue", mesh=Mesh(name="tongue", vertices=_flat(verts), faces=faces))


def _build_laces() -> Node:
    """Return a folder of lace-strip quads."""
    # Four diagonal strips across the instep.
    lace_centers_z = [0.05, 0.25, 0.45, 0.65]
    lace_nodes: list[Node] = []
    for idx, cz in enumerate(lace_centers_z):
        width = 0.18
        half_h = 0.03
        y = 0.16 + 0.04 * idx  # rise toward toe
        verts: list[Vec3] = [
            (cz - half_h, y, -width / 2),
            (cz + half_h, y, width / 2),
            (cz + half_h, y + 0.03, width / 2),
            (cz - half_h, y + 0.03, -width / 2),
        ]
        all_v = verts
        faces: list[Face] = [
            Face(
                vertex_ids=ensure_outward([0, 1, 2, 3], all_v),
                uvs=project_uv([0, 1, 2, 3], all_v, _tile(6, 7)),
                color=1,
                dbl=True,
            )
        ]
        lace_nodes.append(
            Node(
                name=f"lace_{idx}",
                mesh=Mesh(name=f"lace_{idx}", vertices=_flat(verts), faces=faces),
            )
        )
    return Node(name="laces", children=lace_nodes)


def _build_stripes() -> Node:
    """Return a folder with three white side stripes on the lateral side."""
    # Lateral side is the left side (negative z in our orientation).
    stripe_data: list[list[Vec3]] = [
        [  # top stripe
            (0.45, 0.02, -0.31),
            (-0.55, 0.08, -0.26),
            (-0.55, 0.12, -0.265),
            (0.45, 0.06, -0.315),
        ],
        [  # middle stripe
            (0.55, -0.10, -0.315),
            (-0.55, -0.02, -0.275),
            (-0.55, 0.02, -0.28),
            (0.55, -0.06, -0.32),
        ],
        [  # bottom stripe
            (0.60, -0.22, -0.32),
            (-0.50, -0.14, -0.285),
            (-0.50, -0.10, -0.29),
            (0.60, -0.18, -0.325),
        ],
    ]
    stripe_nodes: list[Node] = []
    for idx, verts in enumerate(stripe_data):
        all_v = verts
        faces: list[Face] = [
            Face(
                vertex_ids=ensure_outward([0, 1, 2, 3], all_v),
                uvs=project_uv([0, 1, 2, 3], all_v, _tile(7, idx)),
                color=1,
                dbl=True,
            )
        ]
        stripe_nodes.append(
            Node(
                name=f"stripe_{idx}",
                mesh=Mesh(name=f"stripe_{idx}", vertices=_flat(verts), faces=faces),
            )
        )
    return Node(name="stripes", children=stripe_nodes)


# ---------------------------------------------------------------------- main


def build_football_shoe_v2() -> Model:
    """Build the football boot v2 :class:`Model`."""
    children: list[Node] = [
        _build_sole(),
        _build_upper(),
        _build_heel_counter(),
        _build_studs(),
        _build_tongue(),
        _build_laces(),
        _build_stripes(),
    ]
    shoe = Node(name="shoe", children=children)
    root = Node(name="root", children=[shoe])

    tex = Texture(background_color=1)

    # Sole plate tiles (rows 0-1)
    tex.paint_tile(_tile_span(0, 0, 4, 2), 6)
    # Triangular grip pattern on sole bottom.
    for row in range(0, 32, 8):
        for px in range(0, 64, 8):
            for k in range(4):
                tex.set_pixel(px + k, row + k, 10)
                tex.set_pixel(px + 7 - k, row + k, 10)
    # Sole side tiles.
    for row, col in [(0, 4), (0, 5), (0, 6), (0, 7), (1, 0), (1, 1), (1, 2), (1, 3)]:
        tex.paint_tile(_tile(row, col), 10)

    # Upper blue panels (rows 2-3)
    tex.paint_tile(_tile_span(2, 0, 2, 1), 2)
    tex.paint_tile(_tile_span(2, 2, 2, 1), 2)
    tex.paint_tile(_tile_span(2, 4, 2, 1), 3)
    tex.paint_tile(_tile_span(2, 6, 2, 1), 3)
    # Stitching dashes.
    for row_off in (32, 40, 48):
        for px in range(0, 64, 4):
            tex.set_pixel(px, row_off + 6, 5)
            tex.set_pixel(px + 1, row_off + 6, 5)

    # Heel back / toe cap tiles (row 4)
    tex.paint_tile(_tile(4, 0), 12)
    tex.paint_tile(_tile(4, 1), 12)
    tex.paint_tile(_tile_span(4, 2, 1, 2), 11)

    # Instep / lace deck white tiles (rows 4-5)
    for rect in [
        _tile_span(4, 3, 1, 2),
        _tile_span(4, 4, 1, 2),
        _tile_span(4, 5, 1, 2),
        _tile_span(5, 0, 1, 2),
        _tile_span(5, 1, 1, 2),
        _tile_span(5, 2, 1, 2),
    ]:
        tex.paint_tile(rect, 1)
    # Dark lace-eyelet dots down the center.
    for ly in (72, 80, 88, 96):
        for lx in (70, 74):
            tex.set_pixel(lx, ly, 0)
            tex.set_pixel(lx + 1, ly, 0)

    # Collar interior.
    tex.paint_tile(_tile(5, 3), 5)

    # Heel counter tiles.
    for rect in [_tile(5, 4), _tile(5, 5), _tile(5, 6), _tile(5, 7), _tile(6, 0)]:
        tex.paint_tile(rect, 12)

    # Stud tiles.
    for col in range(1, 5):
        tex.paint_tile(_tile(6, col), 7)

    # Tongue tile.
    tex.paint_tile(_tile_span(6, 5, 1, 2), 1)

    # Lace tile.
    tex.paint_tile(_tile(6, 7), 1)

    # Stripe tiles.
    for col in range(3):
        tex.paint_tile(_tile(7, col), 1)

    return Model(
        root=root,
        texture=tex,
        colors=BOOT_COLORS,
        shade_pal_1=BOOT_SHADE_PAL_1,
        shade_pal_2=BOOT_SHADE_PAL_2,
        background_color=1,
        transparent_color=14,
        shading_mode=1,
        motion_duration=2,
        camera=Camera(
            pos=(3.2, 1.6, 3.6),
            target=(0.0, -0.05, 0.0),
            distance_to_target=5.2,
            omega=-0.85,
            theta=0.38,
        ),
    )


def _count_faces(node: Node) -> int:
    """Recursively count faces under a node."""
    count = len(node.mesh.faces) if node.mesh is not None else 0
    for child in node.children:
        count += _count_faces(child)
    return count


def _count_verts(node: Node) -> int:
    """Recursively count vertices under a node."""
    count = len(node.mesh.vertices) // 3 if node.mesh is not None else 0
    for child in node.children:
        count += _count_verts(child)
    return count


def main() -> None:
    """Write ``models/football_shoe/<name>.txt``."""
    model = build_football_shoe_v2()
    script_name = Path(__file__).resolve().name
    model_name = script_name.removeprefix("gen_").replace(".py", ".txt")
    out_path = (
        Path(__file__).resolve().parent.parent.parent / "models" / "football_shoe" / model_name
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.write(out_path)
    print(f"wrote {out_path}")
    print(f"verts={_count_verts(model.root)} faces={_count_faces(model.root)}")


if __name__ == "__main__":
    main()
