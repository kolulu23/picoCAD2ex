"""Recipe: low-poly football shoe (soccer cleat) for picoCAD 2.

A blue-and-white football shoe with realistic texture details:
- Sole plate with blade-stud grip pattern
- Perforated upper panels for breathability
- White brand stripes on lateral side
- Lace eyelets and tongue
- Heel counter with pull tab
- Stitching detail on seams

The shoe points along +X (toe) / -X (heel), Y-up.

Run::

    uv run python scripts/football_shoe/gen_football_shoe_opencode.py

Outputs ``models/football_shoe_opencode.txt``.
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
    """Return UV tile rect for (row, col) in 8x8 grid."""
    u0 = col * TILE
    v0 = row * TILE
    return (u0, v0, u0 + TILE, v0 + TILE)


def _tile_span(row: int, col: int, w: int, h: int) -> tuple[float, float, float, float]:
    """Return a tile spanning w cols x h rows starting at (row, col)."""
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
# Blue + white football shoe palette, 16 slots.
# Slot 14 = transparent (reserved). Background = slot 9 (warm sand).
SHOE_COLORS: list[Vec3] = [
    (0.02, 0.02, 0.04),  #  0 near-black (outlines, eyelets)
    (0.96, 0.96, 0.97),  #  1 white (sole, stripes, laces)
    (0.12, 0.36, 0.78),  #  2 royal blue (main upper)
    (0.06, 0.18, 0.48),  #  3 dark blue (shaded upper)
    (0.30, 0.55, 0.92),  #  4 sky blue (lit upper highlight)
    (0.02, 0.08, 0.22),  #  5 deep navy (liner, deepest shadow)
    (0.72, 0.74, 0.78),  #  6 silver (sole plate, studs)
    (0.40, 0.42, 0.46),  #  7 gunmetal (stud shadow)
    (0.88, 0.90, 0.92),  #  8 bright silver (stud highlight)
    (0.82, 0.76, 0.68),  #  9 warm sand (BACKGROUND)
    (0.55, 0.58, 0.62),  # 10 mid gray (sole edge detail)
    (0.22, 0.24, 0.28),  # 11 charcoal (grip lines, dark accents)
    (0.08, 0.28, 0.62),  # 12 medium blue (toe cap, heel counter)
    (0.92, 0.93, 0.94),  # 13 off-white
    (1.00, 1.00, 1.00),  # 14 transparent (reserved)
    (0.18, 0.48, 0.88),  # 15 vivid blue (accent highlights)
]

# Lit-side shade ramp: map base color to lit variant.
SHOE_SHADE_PAL_1: list[int] = [
    0,  # 0 near-black
    13,  # 1 white -> off-white
    4,  # 2 royal blue -> sky blue
    2,  # 3 dark blue -> royal blue
    4,  # 4 sky blue
    3,  # 5 deep navy -> dark blue
    8,  # 6 silver -> bright silver
    6,  # 7 gunmetal -> silver
    8,  # 8 bright silver
    9,  # 9 warm sand
    6,  # 10 mid gray -> silver
    7,  # 11 charcoal -> gunmetal
    2,  # 12 medium blue -> royal blue
    1,  # 13 off-white -> white
    14,  # 14 transparent
    4,  # 15 vivid blue -> sky blue
]

# Shadow-side ramp.
SHOE_SHADE_PAL_2: list[int] = [
    0,  # 0 near-black
    6,  # 1 white -> silver (ambient reflection in shadow)
    3,  # 2 royal blue -> dark blue
    5,  # 3 dark blue -> deep navy
    2,  # 4 sky blue -> royal blue
    0,  # 5 deep navy -> near-black
    7,  # 6 silver -> gunmetal
    11,  # 7 gunmetal -> charcoal
    6,  # 8 bright silver -> silver
    9,  # 9 warm sand
    11,  # 10 mid gray -> charcoal
    0,  # 11 charcoal -> near-black
    3,  # 12 medium blue -> dark blue
    10,  # 13 off-white -> mid gray
    14,  # 14 transparent
    3,  # 15 vivid blue -> dark blue
]


# --------------------------------------------------------------------- parts
def _build_sole() -> Node:
    """Build the sole plate with bottom, top, and side walls."""
    # 9-point profile: bottom ring, top ring, toe tip.
    bottom: list[Vec3] = [
        (-1.10, -0.52, -0.18),  # 0 heel-L
        (-0.40, -0.54, -0.30),  # 1 arch-L
        (0.25, -0.52, -0.28),  # 2 fore-L
        (0.80, -0.48, -0.18),  # 3 toe-L
        (1.05, -0.44, 0.00),  # 4 toe-tip
        (0.80, -0.48, 0.18),  # 5 toe-R
        (0.25, -0.52, 0.28),  # 6 fore-R
        (-0.40, -0.54, 0.30),  # 7 arch-R
        (-1.10, -0.52, 0.18),  # 8 heel-R
    ]
    top: list[Vec3] = [
        (-1.10, -0.38, -0.18),  # 9
        (-0.40, -0.38, -0.30),  # 10
        (0.25, -0.36, -0.28),  # 11
        (0.80, -0.34, -0.18),  # 12
        (1.05, -0.32, 0.00),  # 13
        (0.80, -0.34, 0.18),  # 14
        (0.25, -0.36, 0.28),  # 15
        (-0.40, -0.38, 0.30),  # 16
        (-1.10, -0.38, 0.18),  # 17
    ]
    verts = bottom + top
    all_v = verts

    faces: list[Face] = []
    # Bottom: 9-gon fan
    faces.append(
        Face(
            vertex_ids=ensure_outward([0, 1, 2, 3, 4, 5, 6, 7, 8], all_v),
            uvs=project_uv([0, 1, 2, 3, 4, 5, 6, 7, 8], all_v, _tile_span(0, 0, 4, 2)),
            color=6,
        )
    )
    # Top: 9-gon fan
    faces.append(
        Face(
            vertex_ids=ensure_outward([9, 10, 11, 12, 13, 14, 15, 16, 17], all_v),
            uvs=project_uv(
                [9, 10, 11, 12, 13, 14, 15, 16, 17],
                all_v,
                _tile_span(0, 0, 4, 2),
            ),
            color=10,
        )
    )
    # Side walls: 9 quads around perimeter
    side_pairs = [
        (0, 1, 10, 9),
        (1, 2, 11, 10),
        (2, 3, 12, 11),
        (3, 4, 13, 12),
        (4, 5, 14, 13),
        (5, 6, 15, 14),
        (6, 7, 16, 15),
        (7, 8, 17, 16),
        (8, 0, 9, 17),
    ]
    side_tiles = [
        _tile(0, 4),
        _tile(0, 5),
        _tile(0, 6),
        _tile(0, 7),
        _tile(1, 0),
        _tile(1, 1),
        _tile(1, 2),
        _tile(1, 3),
        _tile(1, 4),
    ]
    for (a, b, c, d), t in zip(side_pairs, side_tiles, strict=True):
        faces.append(
            Face(
                vertex_ids=ensure_outward([a, b, c, d], all_v),
                uvs=project_uv([a, b, c, d], all_v, t),
                color=11,
            )
        )

    mesh = Mesh(name="sole", vertices=_flat(verts), faces=faces)
    return Node(name="sole", mesh=mesh)


def _build_upper() -> Node:
    """Build the upper boot body with three rings."""
    # Bottom ring (sits on sole top, y=-0.38)
    btm: list[Vec3] = [
        (-1.10, -0.38, -0.18),  # 0 heel-L
        (-0.40, -0.38, -0.30),  # 1 arch-L
        (0.25, -0.36, -0.28),  # 2 fore-L
        (0.80, -0.34, -0.18),  # 3 toe-L
        (1.05, -0.32, 0.00),  # 4 toe-tip
        (0.80, -0.34, 0.18),  # 5 toe-R
        (0.25, -0.36, 0.28),  # 6 fore-R
        (-0.40, -0.38, 0.30),  # 7 arch-R
        (-1.10, -0.38, 0.18),  # 8 heel-R
    ]
    # Mid ring (y ~ 0.0)
    mid: list[Vec3] = [
        (-1.10, 0.00, -0.16),  # 9
        (-0.45, 0.00, -0.28),  # 10
        (0.20, 0.02, -0.24),  # 11
        (0.72, 0.04, -0.14),  # 12
        (0.95, 0.06, 0.00),  # 13
        (0.72, 0.04, 0.14),  # 14
        (0.20, 0.02, 0.24),  # 15
        (-0.45, 0.00, 0.28),  # 16
        (-1.10, 0.00, 0.16),  # 17
    ]
    # Collar ring (y ~ 0.16)
    collar: list[Vec3] = [
        (-1.10, 0.16, -0.14),  # 18
        (-0.50, 0.10, -0.24),  # 19
        (0.10, 0.12, -0.20),  # 20
        (0.50, 0.14, -0.10),  # 21
        (0.65, 0.16, 0.00),  # 22
        (0.50, 0.14, 0.10),  # 23
        (0.10, 0.12, 0.20),  # 24
        (-0.50, 0.10, 0.24),  # 25
        (-1.10, 0.16, 0.14),  # 26
    ]
    # Toe cap tip
    toe_tip: Vec3 = (1.18, -0.20, 0.0)  # 27

    verts = btm + mid + collar + [toe_tip]
    all_v = verts

    faces: list[Face] = []
    # Left wall: btm->mid (sections 0-3)
    for i in range(4):
        j = i + 1
        faces.append(
            Face(
                vertex_ids=ensure_outward([i, j, j + 9, i + 9], all_v),
                uvs=project_uv([i, j, j + 9, i + 9], all_v, _tile_span(2, 0, 2, 1)),
                color=2,
            )
        )
    # Left wall: mid->collar (sections 0-3)
    for i in range(4):
        j = i + 1
        faces.append(
            Face(
                vertex_ids=ensure_outward([i + 9, j + 9, j + 18, i + 18], all_v),
                uvs=project_uv(
                    [i + 9, j + 9, j + 18, i + 18],
                    all_v,
                    _tile_span(2, 2, 2, 1),
                ),
                color=2,
            )
        )
    # Right wall: btm->mid (sections 5-8)
    for i in range(5, 9):
        j = (i + 1) % 9
        faces.append(
            Face(
                vertex_ids=ensure_outward([i, j, j + 9, i + 9], all_v),
                uvs=project_uv([i, j, j + 9, i + 9], all_v, _tile_span(2, 4, 2, 1)),
                color=3,
            )
        )
    # Right wall: mid->collar (sections 5-8)
    for i in range(5, 9):
        j = (i + 1) % 9
        faces.append(
            Face(
                vertex_ids=ensure_outward([i + 9, j + 9, j + 18, i + 18], all_v),
                uvs=project_uv(
                    [i + 9, j + 9, j + 18, i + 18],
                    all_v,
                    _tile_span(2, 6, 2, 1),
                ),
                color=3,
            )
        )

    # Toe box sides: sections 3->4 (toe-L to tip) and 4->5 (tip to toe-R)
    # Left toe side: btm->mid
    faces.append(
        Face(
            vertex_ids=ensure_outward([3, 4, 13, 12], all_v),
            uvs=project_uv([3, 4, 13, 12], all_v, _tile_span(4, 0, 1, 2)),
            color=2,
        )
    )
    # Left toe side: mid->collar
    faces.append(
        Face(
            vertex_ids=ensure_outward([12, 13, 22, 21], all_v),
            uvs=project_uv([12, 13, 22, 21], all_v, _tile_span(4, 0, 1, 2)),
            color=2,
        )
    )
    # Right toe side: btm->mid
    faces.append(
        Face(
            vertex_ids=ensure_outward([4, 5, 14, 13], all_v),
            uvs=project_uv([4, 5, 14, 13], all_v, _tile_span(4, 0, 1, 2)),
            color=3,
        )
    )
    # Right toe side: mid->collar
    faces.append(
        Face(
            vertex_ids=ensure_outward([13, 14, 23, 22], all_v),
            uvs=project_uv([13, 14, 23, 22], all_v, _tile_span(4, 0, 1, 2)),
            color=3,
        )
    )
    # Toe cap front face
    faces.append(
        Face(
            vertex_ids=ensure_outward([4, 13, 22, 27], all_v),
            uvs=project_uv([4, 13, 22, 27], all_v, _tile_span(4, 0, 1, 2)),
            color=12,
        )
    )
    # Heel back
    faces.append(
        Face(
            vertex_ids=ensure_outward([8, 0, 9, 17], all_v),
            uvs=project_uv([8, 0, 9, 17], all_v, _tile(4, 2)),
            color=12,
        )
    )
    faces.append(
        Face(
            vertex_ids=ensure_outward([17, 9, 18, 26], all_v),
            uvs=project_uv([17, 9, 18, 26], all_v, _tile(4, 3)),
            color=12,
        )
    )

    # Instep left (collar->mid): 3 quads
    instep_left = [
        (18, 19, 10, 9),
        (19, 20, 11, 10),
        (20, 21, 12, 11),
    ]
    for vids in instep_left:
        faces.append(
            Face(
                vertex_ids=ensure_outward(list(vids), all_v),
                uvs=project_uv(list(vids), all_v, _tile_span(4, 4, 1, 2)),
                color=1,
            )
        )
    # Instep left toe front: section 3->4 (collar->mid)
    faces.append(
        Face(
            vertex_ids=ensure_outward([21, 22, 13, 12], all_v),
            uvs=project_uv([21, 22, 13, 12], all_v, _tile_span(4, 4, 1, 2)),
            color=1,
        )
    )

    # Instep right: 3 quads
    instep_right = [
        (23, 24, 15, 14),
        (24, 25, 16, 15),
        (25, 26, 17, 16),
    ]
    for vids in instep_right:
        faces.append(
            Face(
                vertex_ids=ensure_outward(list(vids), all_v),
                uvs=project_uv(list(vids), all_v, _tile_span(5, 0, 1, 2)),
                color=1,
            )
        )
    # Instep right toe front: section 4->5 (collar->mid)
    faces.append(
        Face(
            vertex_ids=ensure_outward([22, 23, 14, 13], all_v),
            uvs=project_uv([22, 23, 14, 13], all_v, _tile_span(5, 0, 1, 2)),
            color=1,
        )
    )

    # Collar rim: 8-gon, dbl=True so opening reads from both sides
    faces.append(
        Face(
            vertex_ids=ensure_outward([18, 26, 25, 24, 23, 22, 21, 20], all_v),
            uvs=project_uv([18, 26, 25, 24, 23, 22, 21, 20], all_v, _tile(5, 2)),
            color=5,
            dbl=True,
        )
    )

    mesh = Mesh(name="upper", vertices=_flat(verts), faces=faces)
    return Node(name="upper", mesh=mesh)


def _build_sock_collar() -> Node:
    """Build the dynamic-fit sock collar rising above the ankle."""
    verts: list[Vec3] = [
        (-1.10, 0.16, -0.14),  # 0 back-L
        (-0.50, 0.10, -0.24),  # 1 side-L
        (0.10, 0.12, -0.20),  # 2 front-L
        (0.10, 0.12, 0.20),  # 3 front-R
        (-0.50, 0.10, 0.24),  # 4 side-R
        (-1.10, 0.16, 0.14),  # 5 back-R
        (-1.10, 0.42, -0.10),  # 6 top-back-L
        (-0.55, 0.36, -0.18),  # 7 top-side-L
        (0.05, 0.38, -0.14),  # 8 top-front-L
        (0.05, 0.38, 0.14),  # 9 top-front-R
        (-0.55, 0.36, 0.18),  # 10 top-side-R
        (-1.10, 0.42, 0.10),  # 11 top-back-R
    ]
    all_v = verts

    faces: list[Face] = []
    # Side walls: 5 quads
    wall_pairs = [
        (0, 1, 7, 6),
        (1, 2, 8, 7),
        (3, 4, 10, 9),
        (4, 5, 11, 10),
        (5, 0, 6, 11),
    ]
    wall_tiles = [
        _tile(5, 3),
        _tile(5, 4),
        _tile(5, 5),
        _tile(5, 6),
        _tile(5, 7),
    ]
    wall_colors = [2, 2, 3, 3, 2]
    for (a, b, c, d), t, col in zip(wall_pairs, wall_tiles, wall_colors, strict=True):
        faces.append(
            Face(
                vertex_ids=ensure_outward([a, b, c, d], all_v),
                uvs=project_uv([a, b, c, d], all_v, t),
                color=col,
                dbl=True,
            )
        )

    # Front opening
    faces.append(
        Face(
            vertex_ids=ensure_outward([2, 3, 9, 8], all_v),
            uvs=project_uv([2, 3, 9, 8], all_v, _tile(6, 0)),
            color=1,
            dbl=True,
        )
    )
    # Top cap
    faces.append(
        Face(
            vertex_ids=ensure_outward([6, 7, 8, 9, 10, 11], all_v),
            uvs=project_uv([6, 7, 8, 9, 10, 11], all_v, _tile(6, 1)),
            color=5,
            dbl=True,
        )
    )

    mesh = Mesh(name="sock_collar", vertices=_flat(verts), faces=faces)
    return Node(name="sock_collar", mesh=mesh)


def _build_heel_counter() -> Node:
    """Build a raised heel-counter shell with pull tab."""
    verts: list[Vec3] = [
        (-1.10, -0.38, -0.18),  # 0
        (-1.10, -0.38, 0.18),  # 1
        (-1.10, 0.00, -0.16),  # 2
        (-1.10, 0.00, 0.16),  # 3
        (-1.14, -0.20, -0.20),  # 4
        (-1.14, -0.20, 0.20),  # 5
    ]
    all_v = verts
    faces: list[Face] = [
        Face(
            vertex_ids=ensure_outward([0, 4, 5, 1], all_v),
            uvs=project_uv([0, 4, 5, 1], all_v, _tile(6, 2)),
            color=12,
        ),
        Face(
            vertex_ids=ensure_outward([0, 2, 4], all_v),
            uvs=project_uv([0, 2, 4], all_v, _tile(6, 3)),
            color=12,
        ),
        Face(
            vertex_ids=ensure_outward([1, 5, 3], all_v),
            uvs=project_uv([1, 5, 3], all_v, _tile(6, 4)),
            color=12,
        ),
        Face(
            vertex_ids=ensure_outward([4, 2, 3, 5], all_v),
            uvs=project_uv([4, 2, 3, 5], all_v, _tile(6, 5)),
            color=3,
            dbl=True,
        ),
    ]
    mesh = Mesh(name="heel_counter", vertices=_flat(verts), faces=faces)
    return Node(name="heel_counter", mesh=mesh)


def _build_studs() -> Node:
    """Build 8 conical studs (4 forefoot, 2 mid, 2 heel)."""
    positions: list[Vec3] = [
        (0.65, -0.52, -0.16),  # forefoot front-L
        (0.65, -0.52, 0.16),  # forefoot front-R
        (0.20, -0.52, -0.22),  # forefoot back-L
        (0.20, -0.52, 0.22),  # forefoot back-R
        (-0.65, -0.52, -0.14),  # mid-L
        (-0.65, -0.52, 0.14),  # mid-R
        (-1.00, -0.52, -0.10),  # heel-L
        (-1.00, -0.52, 0.10),  # heel-R
    ]
    stud_nodes: list[Node] = []
    for idx, base in enumerate(positions):
        bx, by, bz = base
        rx, rz, h = 0.06, 0.04, 0.10
        cv: list[Vec3] = [
            (bx - rx, by, bz - rz),
            (bx + rx, by, bz - rz),
            (bx + rx, by, bz + rz),
            (bx - rx, by, bz + rz),
            (bx, by - h, bz),
        ]
        all_cv = cv
        cf: list[Face] = [
            Face(
                vertex_ids=ensure_outward([0, 1, 4], all_cv),
                uvs=project_uv([0, 1, 4], all_cv, _tile(6, 6 + (idx % 2))),
                color=7,
            ),
            Face(
                vertex_ids=ensure_outward([1, 2, 4], all_cv),
                uvs=project_uv([1, 2, 4], all_cv, _tile(6, 6 + ((idx + 1) % 2))),
                color=8,
            ),
            Face(
                vertex_ids=ensure_outward([2, 3, 4], all_cv),
                uvs=project_uv([2, 3, 4], all_cv, _tile(6, 6 + ((idx + 2) % 2))),
                color=8,
            ),
            Face(
                vertex_ids=ensure_outward([3, 0, 4], all_cv),
                uvs=project_uv([3, 0, 4], all_cv, _tile(6, 6 + ((idx + 3) % 2))),
                color=7,
            ),
        ]
        stud_nodes.append(
            Node(
                name=f"stud_{idx}",
                mesh=Mesh(
                    name=f"stud_{idx}",
                    vertices=_flat(cv),
                    faces=cf,
                ),
            )
        )
    return Node(name="studs", children=stud_nodes)


def _build_tongue() -> Node:
    """Build the tongue flap rising from the instep."""
    verts: list[Vec3] = [
        (0.10, 0.12, -0.16),  # 0 base-L
        (0.10, 0.12, 0.16),  # 1 base-R
        (0.55, 0.30, -0.08),  # 2 tip-L
        (0.55, 0.30, 0.08),  # 3 tip-R
    ]
    all_v = verts
    faces: list[Face] = [
        Face(
            vertex_ids=ensure_outward([0, 1, 3, 2], all_v),
            uvs=project_uv([0, 1, 3, 2], all_v, _tile_span(7, 0, 1, 2)),
            color=1,
            dbl=True,
        )
    ]
    return Node(
        name="tongue",
        mesh=Mesh(name="tongue", vertices=_flat(verts), faces=faces),
    )


def _build_laces() -> Node:
    """Build 4 diagonal lace strips across the instep."""
    lace_nodes: list[Node] = []
    z_positions = [-0.10, -0.02, 0.06, 0.14]
    for idx, zc in enumerate(z_positions):
        hw = 0.06
        hh = 0.015
        x0 = 0.18 + idx * 0.10
        x1 = x0 + 0.04
        y = 0.14 + idx * 0.03
        verts: list[Vec3] = [
            (x0, y, zc - hw),
            (x1, y, zc + hw),
            (x1, y + hh, zc + hw),
            (x0, y + hh, zc - hw),
        ]
        all_v = verts
        faces: list[Face] = [
            Face(
                vertex_ids=ensure_outward([0, 1, 2, 3], all_v),
                uvs=project_uv([0, 1, 2, 3], all_v, _tile(7, 2)),
                color=1,
                dbl=True,
            )
        ]
        lace_nodes.append(
            Node(
                name=f"lace_{idx}",
                mesh=Mesh(
                    name=f"lace_{idx}",
                    vertices=_flat(verts),
                    faces=faces,
                ),
            )
        )
    return Node(name="laces", children=lace_nodes)


def _build_stripes() -> Node:
    """Build 3 white diagonal stripes on the lateral side."""
    stripe_data: list[list[Vec3]] = [
        [
            (0.40, 0.02, -0.29),
            (-0.50, 0.08, -0.24),
            (-0.50, 0.12, -0.245),
            (0.40, 0.06, -0.295),
        ],
        [
            (0.50, -0.10, -0.295),
            (-0.50, -0.02, -0.255),
            (-0.50, 0.02, -0.26),
            (0.50, -0.06, -0.30),
        ],
        [
            (0.55, -0.22, -0.30),
            (-0.45, -0.14, -0.265),
            (-0.45, -0.10, -0.27),
            (0.55, -0.18, -0.305),
        ],
    ]
    stripe_nodes: list[Node] = []
    for idx, verts in enumerate(stripe_data):
        all_v = verts
        faces: list[Face] = [
            Face(
                vertex_ids=ensure_outward([0, 1, 2, 3], all_v),
                uvs=project_uv([0, 1, 2, 3], all_v, _tile(7, 3 + idx)),
                color=1,
                dbl=True,
            )
        ]
        stripe_nodes.append(
            Node(
                name=f"stripe_{idx}",
                mesh=Mesh(
                    name=f"stripe_{idx}",
                    vertices=_flat(verts),
                    faces=faces,
                ),
            )
        )
    return Node(name="stripes", children=stripe_nodes)


# ----------------------------------------------------------------- texture
def _paint_texture() -> Texture:
    """Paint the 128x128 texture with realistic football shoe details."""
    tex = Texture(background_color=9)

    # --- Sole plate (rows 0-1, cols 0-3) ---
    tex.paint_tile(_tile_span(0, 0, 4, 2), 6)
    # Grip lines on sole bottom
    for row in range(0, 32, 3):
        for px in range(2, 62, 2):
            tex.set_pixel(px, row, 11)
    # Sole plate channels
    for col_px in range(4, 60, 8):
        for row_px in range(2, 30):
            tex.set_pixel(col_px, row_px, 10)
            tex.set_pixel(col_px + 1, row_px, 10)

    # --- Sole side walls (rows 0-1, cols 4-7) ---
    for row, col in [
        (0, 4),
        (0, 5),
        (0, 6),
        (0, 7),
        (1, 0),
        (1, 1),
        (1, 2),
        (1, 3),
        (1, 4),
    ]:
        tex.paint_tile(_tile(row, col), 11)
    # Grip texture on sides
    for row_px in range(4, 28, 6):
        for px in range(64, 128):
            tex.set_pixel(px - 64 + (row * 16 if row < 4 else 0), row_px, 7)

    # --- Upper blue panels (rows 2-3) ---
    tex.paint_tile(_tile_span(2, 0, 2, 1), 2)
    tex.paint_tile(_tile_span(2, 2, 2, 1), 2)
    tex.paint_tile(_tile_span(2, 4, 2, 1), 3)
    tex.paint_tile(_tile_span(2, 6, 2, 1), 3)
    # Stitching dashes on left panels
    for row_off in (32, 34, 36, 38, 40, 42, 44, 46):
        for px in range(0, 64, 6):
            tex.set_pixel(px, row_off, 5)
            tex.set_pixel(px + 1, row_off, 5)
    # Perforations on left panels (breathability holes)
    for row_off in range(33, 47, 4):
        for px in range(2, 62, 3):
            tex.set_pixel(px, row_off, 4)
    # Stitching on right panels
    for row_off in (32, 34, 36, 38, 40, 42, 44, 46):
        for px in range(64, 128, 6):
            tex.set_pixel(px, row_off, 5)
            tex.set_pixel(px + 1, row_off, 5)

    # --- Toe cap / heel back (row 4) ---
    tex.paint_tile(_tile_span(4, 0, 1, 2), 12)
    tex.paint_tile(_tile(4, 2), 12)
    tex.paint_tile(_tile(4, 3), 12)

    # --- Instep / lace deck white panels (rows 4-5) ---
    for rect in [
        _tile_span(4, 4, 1, 2),
        _tile_span(5, 0, 1, 2),
    ]:
        tex.paint_tile(rect, 1)
    # Lace eyelets (dark dots)
    for ly in (68, 74, 80, 86):
        for lx_off in (66, 70):
            tex.set_pixel(lx_off, ly, 0)
            tex.set_pixel(lx_off + 1, ly, 0)
            tex.set_pixel(lx_off, ly + 1, 0)
            tex.set_pixel(lx_off + 1, ly + 1, 0)

    # --- Collar interior (row 5, col 2) ---
    tex.paint_tile(_tile(5, 2), 5)

    # --- Sock collar walls (row 5, cols 3-7) ---
    for t in [_tile(5, 3), _tile(5, 4), _tile(5, 5), _tile(5, 6), _tile(5, 7)]:
        tex.paint_tile(t, 2)
    # Collar stitching
    for px in range(80, 94):
        tex.set_pixel(px, 84, 15)
        tex.set_pixel(px, 85, 15)

    # --- Collar front opening (row 6, col 0) ---
    tex.paint_tile(_tile(6, 0), 1)
    # Collar top (row 6, col 1)
    tex.paint_tile(_tile(6, 1), 6)

    # --- Heel counter (row 6, cols 2-5) ---
    for t in [_tile(6, 2), _tile(6, 3), _tile(6, 4), _tile(6, 5)]:
        tex.paint_tile(t, 1)
    # Pull tab stripe
    for px in range(32, 48):
        tex.set_pixel(px, 100, 12)
        tex.set_pixel(px, 101, 12)

    # --- Stud tiles (row 6, cols 6-7) ---
    tex.paint_tile(_tile_span(6, 6, 2, 1), 7)
    for px in range(96, 128, 4):
        tex.set_pixel(px, 100, 8)
        tex.set_pixel(px + 1, 100, 8)

    # --- Tongue (row 7, cols 0-1) ---
    tex.paint_tile(_tile_span(7, 0, 1, 2), 1)
    # Tongue stitching
    for px in range(0, 16, 2):
        tex.set_pixel(px, 114, 0)
        tex.set_pixel(px + 1, 114, 0)
        tex.set_pixel(px, 126, 0)
        tex.set_pixel(px + 1, 126, 0)

    # --- Lace tile (row 7, col 2) ---
    tex.paint_tile(_tile(7, 2), 1)

    # --- Stripe tiles (row 7, cols 3-5) ---
    for col in range(3, 6):
        tex.paint_tile(_tile(7, col), 1)

    return tex


# ---------------------------------------------------------------------- main
def build_football_shoe() -> Model:
    """Build the football shoe model."""
    children: list[Node] = [
        _build_sole(),
        _build_upper(),
        _build_sock_collar(),
        _build_heel_counter(),
        _build_studs(),
        _build_tongue(),
        _build_laces(),
        _build_stripes(),
    ]
    shoe = Node(name="shoe", children=children)
    root = Node(name="root", children=[shoe])

    tex = _paint_texture()

    return Model(
        root=root,
        texture=tex,
        colors=SHOE_COLORS,
        shade_pal_1=SHOE_SHADE_PAL_1,
        shade_pal_2=SHOE_SHADE_PAL_2,
        background_color=9,
        transparent_color=14,
        shading_mode=1,
        motion_duration=2,
        camera=Camera(
            pos=(3.5, 1.8, 3.8),
            target=(0.0, -0.05, 0.0),
            distance_to_target=5.5,
            omega=-0.80,
            theta=0.40,
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
    """Write models/football_shoe/<name>.txt."""
    model = build_football_shoe()
    script_name = Path(__file__).resolve().name
    model_name = script_name.removeprefix("gen_").replace(".py", ".txt")
    out_path = (
        Path(__file__).resolve().parent.parent.parent / "models" / "football_shoe" / model_name
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.write(out_path)
    print(f"wrote {out_path}")
    print(f"verts={_count_verts(model.root)} faces={_count_faces(model.root)}")
    print("parts: sole, upper, sock_collar, heel_counter, 8x studs, tongue, 4x laces, 3x stripes")


if __name__ == "__main__":
    main()
