"""Recipe: low-poly football shoe (soccer cleat) for picoCAD 2.

Generates a stylised football shoe with blue upper, white sole, cleats,
and texture detail (lace eyelets, brand stripes, sole grip pattern).
The shoe points along +X (toe) / -X (heel), Y-up.

Run::

    uv run python scripts/gen_football_shoe.py

Outputs ``models/football_shoe.txt``.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from picocad.model import Camera, Face, Mesh, Model, Node, Transform
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


# ------------------------------------------------------------------- palette
# Blue + white football shoe palette, 16 slots.
# Slot 14 = transparent (reserved).
FOOTBALL_SHOE_COLORS: list[Vec3] = [
    (0.00, 0.00, 0.00),  #  0 black (accents, outlines)
    (0.98, 0.98, 0.98),  #  1 white (sole, stripes, laces)
    (0.15, 0.35, 0.70),  #  2 mid blue (main upper)
    (0.08, 0.20, 0.50),  #  3 dark blue (upper shade side)
    (0.22, 0.50, 0.85),  #  4 light blue (upper lit side)
    (0.05, 0.12, 0.35),  #  5 deepest blue
    (0.75, 0.80, 0.85),  #  6 silver/gray (cleat studs, sole plate)
    (0.35, 0.38, 0.42),  #  7 dark silver (cleat shade)
    (0.85, 0.88, 0.90),  #  8 light silver (cleat highlight)
    (0.90, 0.92, 0.95),  #  9 off-white
    (0.50, 0.55, 0.60),  # 10 mid gray (sole detail)
    (0.30, 0.32, 0.35),  # 11 dark gray (sole shade)
    (0.10, 0.45, 0.80),  # 12 vivid blue (brand accent)
    (0.03, 0.06, 0.18),  # 13 navy (deepest)
    (1.00, 1.00, 1.00),  # 14 transparent (reserved)
    (0.95, 0.95, 0.97),  # 15 near-white
]

# Lit-side shade ramp: map each base color to its lit variant.
FOOTBALL_SHOE_SHADE_PAL_1: list[int] = [
    0,  # 0 black -> black
    1,  # 1 white -> white
    4,  # 2 mid-blue -> light blue
    2,  # 3 dark-blue -> mid-blue (lit side lifts it)
    4,  # 4 light-blue -> light-blue
    3,  # 5 deepest -> dark-blue
    8,  # 6 silver -> light silver
    6,  # 7 dark silver -> silver
    8,  # 8 light silver -> light silver
    9,  # 9 off-white -> off-white
    6,  # 10 mid gray -> silver
    10,  # 11 dark gray -> mid gray
    4,  # 12 vivid blue -> light blue
    3,  # 13 navy -> dark blue
    14,  # 14 transparent
    15,  # 15 near-white
]

# Shadow-side ramp.
FOOTBALL_SHOE_SHADE_PAL_2: list[int] = [
    0,  # 0 black -> black
    9,  # 1 white -> off-white
    3,  # 2 mid-blue -> dark-blue
    5,  # 3 dark-blue -> deepest
    2,  # 4 light-blue -> mid-blue (shadow darkens it)
    5,  # 5 deepest -> deepest
    7,  # 6 silver -> dark silver
    11,  # 7 dark silver -> dark gray
    6,  # 8 light silver -> silver
    1,  # 9 off-white -> white (shadow picks up ambient)
    11,  # 10 mid gray -> dark gray
    11,  # 11 dark gray -> dark gray
    3,  # 12 vivid blue -> dark blue
    5,  # 13 navy -> deepest
    14,  # 14 transparent
    9,  # 15 near-white -> off-white
]


def _flat(verts: Sequence[Vec3]) -> list[float]:
    """Flatten [(x,y,z), ...] into [x,y,z, x,y,z, ...]."""
    out: list[float] = []
    for v in verts:
        out.extend(v)
    return out


def build_football_shoe() -> Model:
    """Build the football shoe model."""
    child_nodes: list[Node] = []

    # ================================================================ SOLE
    # Sole has a 6-ring top/bottom profile matching the upper's bottom ring,
    # with slight z-overhang for a natural sole lip. 14 verts total.
    # Top ring (y = -0.4) — sits flush under the upper bottom ring.
    sg: list[Vec3] = [  # indices 0..5
        (-1.0, -0.4, -0.25),  # 0 heel-left (wider z than upper)
        (0.3, -0.4, -0.36),  # 1 mid-left
        (0.72, -0.38, -0.32),  # 2 toe-left
        (0.72, -0.38, 0.32),  # 3 toe-right
        (0.3, -0.4, 0.36),  # 4 mid-right
        (-1.0, -0.4, 0.25),  # 5 heel-right
    ]
    # Bottom ring (y = -0.55) — same footprint, lower.
    sb: list[Vec3] = [  # indices 6..11
        (-1.0, -0.55, -0.25),  # 6  heel-left-bottom
        (0.3, -0.55, -0.36),  # 7  mid-left-bottom
        (0.72, -0.55, -0.32),  # 8  toe-left-bottom
        (0.72, -0.55, 0.32),  # 9  toe-right-bottom
        (0.3, -0.55, 0.36),  # 10 mid-right-bottom
        (-1.0, -0.55, 0.25),  # 11 heel-right-bottom
    ]
    s_tip_top: Vec3 = (1.08, -0.38, 0.0)  # 12 toe-tip-top
    s_tip_btm: Vec3 = (1.08, -0.52, 0.0)  # 13 toe-tip-bottom

    sole_verts = sg + sb + [s_tip_top, s_tip_btm]
    all_sv = sole_verts

    sole_faces: list[Face] = []

    # Sole bottom — 6-triangle fan from bottom tip (13) along bottom ring (6..11).
    _sb_fan = [
        [6, 7, 13],
        [7, 8, 13],
        [8, 9, 13],
        [9, 10, 13],
        [10, 11, 13],
        [11, 6, 13],
    ]
    for tri in _sb_fan:
        sole_faces.append(
            Face(
                vertex_ids=ensure_outward(tri, all_sv),
                uvs=project_uv(tri, all_sv, _tile_span(0, 0, 4, 3)),
                color=6,
            )
        )

    # Sole top — 6-triangle fan from top tip (12) along top ring (0..5).
    _st_fan = [
        [0, 1, 12],
        [1, 2, 12],
        [2, 3, 12],
        [3, 4, 12],
        [4, 5, 12],
        [5, 0, 12],
    ]
    for tri in _st_fan:
        sole_faces.append(
            Face(
                vertex_ids=ensure_outward(tri, all_sv),
                uvs=project_uv(tri, all_sv, _tile_span(0, 0, 4, 3)),
                color=10,
            )
        )

    # Sole side walls — 5 quads around the perimeter + toe-front pentagon.
    _sw_quads = [
        ([0, 1, 7, 6], _tile(0, 3)),  # left heel-to-mid
        ([1, 2, 8, 7], _tile(0, 4)),  # left mid-to-toe
        ([3, 4, 10, 9], _tile(0, 5)),  # right toe-to-mid
        ([4, 5, 11, 10], _tile(0, 6)),  # right mid-to-heel
        ([5, 0, 6, 11], _tile(0, 7)),  # heel back
    ]
    for vids, tile in _sw_quads:
        sole_faces.append(
            Face(
                vertex_ids=ensure_outward(vids, all_sv),
                uvs=project_uv(vids, all_sv, tile),
                color=11,
            )
        )

    # Sole toe front pentagon: top-toe (2,3) → bottom-toe (8,9) → bottom-tip (13).
    sole_faces.append(
        Face(
            vertex_ids=ensure_outward([2, 3, 9, 13, 8], all_sv),
            uvs=project_uv([2, 3, 9, 13, 8], all_sv, _tile_span(6, 0, 1, 2)),
            color=7,
        )
    )

    sole_mesh = Mesh(name="sole", vertices=_flat(sole_verts), faces=sole_faces)
    child_nodes.append(Node(name="sole", mesh=sole_mesh))

    # ================================================================ UPPER
    # The upper body wraps from sole-top ring up to ankle collar ring.
    # Bottom ring (rests on sole top, y=-0.4):
    ub: list[Vec3] = [
        (-1.0, -0.4, -0.22),  # 0 heel-left
        (0.3, -0.4, -0.32),  # 1 mid-left
        (0.7, -0.38, -0.28),  # 2 toe-left
        (0.7, -0.38, 0.28),  # 3 toe-right
        (0.3, -0.4, 0.32),  # 4 mid-right
        (-1.0, -0.4, 0.22),  # 5 heel-right
    ]
    # Mid ring (y ~ 0.0):
    um: list[Vec3] = [
        (-1.0, 0.0, -0.2),  # 6 heel-left-mid
        (0.15, 0.0, -0.3),  # 7 mid-left-mid
        (0.55, 0.02, -0.26),  # 8 toe-left-mid
        (0.55, 0.02, 0.26),  # 9 toe-right-mid
        (0.15, 0.0, 0.3),  # 10 mid-right-mid
        (-1.0, 0.0, 0.2),  # 11 heel-right-mid
    ]
    # Ankle collar ring (y ~ 0.18):
    uc: list[Vec3] = [
        (-1.0, 0.18, -0.18),  # 12 heel-left-top
        (0.05, 0.12, -0.28),  # 13 mid-left-top
        (0.45, 0.14, -0.24),  # 14 toe-left-top
        (0.45, 0.14, 0.24),  # 15 toe-right-top
        (0.05, 0.12, 0.28),  # 16 mid-right-top
        (-1.0, 0.18, 0.18),  # 17 heel-right-top
    ]
    # Toe box tip:
    toe_tip_up: Vec3 = (1.05, -0.3, 0.0)  # 18

    upper_verts = ub + um + uc + [toe_tip_up]
    all_uv = upper_verts

    upper_faces: list[Face] = []

    # Left body wall: 3 quads connecting bottom -> mid -> collar
    # heel-left quad
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([0, 1, 7, 6], all_uv),
            uvs=project_uv([0, 1, 7, 6], all_uv, _tile_span(1, 0, 2, 1)),
            color=2,
        )
    )
    # mid-left quad
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([1, 2, 8, 7], all_uv),
            uvs=project_uv([1, 2, 8, 7], all_uv, _tile_span(1, 0, 2, 1)),
            color=2,
        )
    )
    # heel-left-mid -> collar
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([6, 7, 13, 12], all_uv),
            uvs=project_uv([6, 7, 13, 12], all_uv, _tile_span(1, 0, 2, 1)),
            color=2,
        )
    )
    # mid-left-mid -> collar
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([7, 8, 14, 13], all_uv),
            uvs=project_uv([7, 8, 14, 13], all_uv, _tile_span(1, 2, 2, 1)),
            color=2,
        )
    )

    # Right body wall: 4 quads using only right-side vertices (3,4,5 / 9,10,11 / 15,16,17)
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([5, 4, 10, 11], all_uv),
            uvs=project_uv([5, 4, 10, 11], all_uv, _tile_span(1, 4, 2, 1)),
            color=3,
        )
    )
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([4, 3, 9, 10], all_uv),
            uvs=project_uv([4, 3, 9, 10], all_uv, _tile_span(1, 4, 2, 1)),
            color=3,
        )
    )
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([11, 10, 16, 17], all_uv),
            uvs=project_uv([11, 10, 16, 17], all_uv, _tile_span(1, 4, 2, 1)),
            color=3,
        )
    )
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([10, 9, 15, 16], all_uv),
            uvs=project_uv([10, 9, 15, 16], all_uv, _tile_span(1, 6, 2, 1)),
            color=3,
        )
    )

    # Heel back: quad [5, 0, 6, 11]
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([5, 0, 6, 11], all_uv),
            uvs=project_uv([5, 0, 6, 11], all_uv, _tile(3, 0)),
            color=3,
        )
    )

    # Heel counter back (above heel): [11, 6, 12, 17]
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([11, 6, 12, 17], all_uv),
            uvs=project_uv([11, 6, 12, 17], all_uv, _tile(3, 1)),
            color=2,
        )
    )

    # Toe box front: [2, 3, 9, 18, 8] — pentagon
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([2, 3, 9, 18, 8], all_uv),
            uvs=project_uv([2, 3, 9, 18, 8], all_uv, _tile_span(3, 2, 1, 2)),
            color=4,
        )
    )

    # Top instep / lace area: 2 quads covering the top between collar opening and toe
    # Front instep quad: [14, 15, 9, 8]
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([14, 15, 9, 8], all_uv),
            uvs=project_uv([14, 15, 9, 8], all_uv, _tile_span(3, 3, 1, 2)),
            color=1,
        )
    )
    # Back instep quad: [13, 14, 8, 7]
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([13, 14, 8, 7], all_uv),
            uvs=project_uv([13, 14, 8, 7], all_uv, _tile_span(3, 3, 1, 2)),
            color=1,
        )
    )
    # Mid instep quad: [12, 13, 7, 6]
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([12, 13, 7, 6], all_uv),
            uvs=project_uv([12, 13, 7, 6], all_uv, _tile_span(3, 5, 1, 1)),
            color=1,
        )
    )

    # Right instep: [16, 15, 9, 10]
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([16, 15, 9, 10], all_uv),
            uvs=project_uv([16, 15, 9, 10], all_uv, _tile_span(4, 0, 1, 2)),
            color=1,
        )
    )
    # Right instep back: [17, 16, 10, 11]
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([17, 16, 10, 11], all_uv),
            uvs=project_uv([17, 16, 10, 11], all_uv, _tile_span(4, 0, 1, 2)),
            color=1,
        )
    )

    # Bottom cap: 6-triangle fan from toe tip (18) to bottom ring (0..5).
    # Closes the upper body so the shoe looks solid from below. dbl=True so the
    # sole top (which sits flush underneath) doesn't make it backface-invisible.
    _ub_fan = [
        [0, 1, 18],
        [1, 2, 18],
        [2, 3, 18],
        [3, 4, 18],
        [4, 5, 18],
        [5, 0, 18],
    ]
    for tri in _ub_fan:
        upper_faces.append(
            Face(
                vertex_ids=ensure_outward(tri, all_uv),
                uvs=project_uv(tri, all_uv, _tile(5, 7)),
                color=5,
                dbl=True,
            )
        )

    # Collar rim face — caps the ankle opening so the inside is visible.
    upper_faces.append(
        Face(
            vertex_ids=ensure_outward([12, 17, 16, 13], all_uv),
            uvs=project_uv([12, 17, 16, 13], all_uv, _tile(4, 2)),
            color=5,
            dbl=True,
        )
    )

    upper_mesh = Mesh(name="upper", vertices=_flat(upper_verts), faces=upper_faces)
    child_nodes.append(Node(name="upper", mesh=upper_mesh))

    # ============================================================ HEEL COUNTER
    # A raised shell at the back of the shoe (above the collar)
    hc_verts: list[Vec3] = [
        (-1.0, 0.18, -0.18),  # 0 collar-left (shared)
        (-0.85, 0.15, -0.22),  # 1 collar-front-left
        (-0.85, 0.15, 0.22),  # 2 collar-front-right
        (-1.0, 0.18, 0.18),  # 3 collar-right (shared)
        (-1.0, 0.38, -0.15),  # 4 heel-counter-top-left
        (-0.85, 0.32, -0.19),  # 5 heel-counter-top-front-left
        (-0.85, 0.32, 0.19),  # 6 heel-counter-top-front-right
        (-1.0, 0.38, 0.15),  # 7 heel-counter-top-right
    ]
    all_hc = hc_verts

    hc_faces: list[Face] = []
    # Left side
    hc_faces.append(
        Face(
            vertex_ids=ensure_outward([0, 1, 5, 4], all_hc),
            uvs=project_uv([0, 1, 5, 4], all_hc, _tile(4, 3)),
            color=2,
        )
    )
    # Right side
    hc_faces.append(
        Face(
            vertex_ids=ensure_outward([2, 3, 7, 6], all_hc),
            uvs=project_uv([2, 3, 7, 6], all_hc, _tile(4, 4)),
            color=3,
        )
    )
    # Back
    hc_faces.append(
        Face(
            vertex_ids=ensure_outward([3, 0, 4, 7], all_hc),
            uvs=project_uv([3, 0, 4, 7], all_hc, _tile(4, 5)),
            color=2,
        )
    )
    # Front (facing forward, connects the collar)
    hc_faces.append(
        Face(
            vertex_ids=ensure_outward([1, 2, 6, 5], all_hc),
            uvs=project_uv([1, 2, 6, 5], all_hc, _tile(4, 5)),
            color=3,
            dbl=True,
        )
    )
    # Top cap
    hc_faces.append(
        Face(
            vertex_ids=ensure_outward([4, 5, 6, 7], all_hc),
            uvs=project_uv([4, 5, 6, 7], all_hc, _tile(4, 6)),
            color=2,
        )
    )

    hc_mesh = Mesh(name="heel_counter", vertices=_flat(hc_verts), faces=hc_faces)
    child_nodes.append(Node(name="heel_counter", mesh=hc_mesh, transform=Transform()))

    # ================================================================ CLEATS
    # 6 studs: 4 forefoot, 2 heel. Each is a small pyramid.
    cleat_positions: list[Vec3] = [
        (0.6, -0.55, -0.2),  # forefoot front-left
        (0.6, -0.55, 0.2),  # forefoot front-right
        (0.1, -0.55, -0.22),  # forefoot back-left
        (0.1, -0.55, 0.22),  # forefoot back-right
        (-0.6, -0.55, -0.17),  # heel-left
        (-0.6, -0.55, 0.17),  # heel-right
    ]
    cleat_nodes: list[Node] = []
    for ci, base_center in enumerate(cleat_positions):
        cx, cy, cz = base_center
        r = 0.06  # half-width of cleat base
        h = 0.1  # height of cleat
        cv: list[Vec3] = [
            (cx - r, cy, cz - r),  # 0 base-bl
            (cx + r, cy, cz - r),  # 1 base-br
            (cx + r, cy, cz + r),  # 2 base-fr
            (cx - r, cy, cz + r),  # 3 base-fl
            (cx, cy - h, cz),  # 4 tip (bottom)
        ]
        all_cv = cv
        cf: list[Face] = []
        # 4 triangular sides
        cf.append(
            Face(
                vertex_ids=ensure_outward([0, 1, 4], all_cv),
                uvs=project_uv([0, 1, 4], all_cv, _tile(5, ci % 4)),
                color=7,
            )
        )
        cf.append(
            Face(
                vertex_ids=ensure_outward([1, 2, 4], all_cv),
                uvs=project_uv([1, 2, 4], all_cv, _tile(5, (ci + 1) % 4)),
                color=7,
            )
        )
        cf.append(
            Face(
                vertex_ids=ensure_outward([2, 3, 4], all_cv),
                uvs=project_uv([2, 3, 4], all_cv, _tile(5, (ci + 2) % 4)),
                color=8,
            )
        )
        cf.append(
            Face(
                vertex_ids=ensure_outward([3, 0, 4], all_cv),
                uvs=project_uv([3, 0, 4], all_cv, _tile(5, (ci + 3) % 4)),
                color=8,
            )
        )
        cleat_mesh = Mesh(name=f"cleat_{ci}", vertices=_flat(cv), faces=cf)
        cleat_nodes.append(Node(name=f"cleat_{ci}", mesh=cleat_mesh))

    # Group cleats under a folder
    cleat_folder = Node(name="cleats", children=cleat_nodes)
    child_nodes.append(cleat_folder)

    # =============================================================== TONGUE
    # A small flap rising from the instep
    tongue_verts: list[Vec3] = [
        (0.25, 0.12, -0.15),  # 0 base-left
        (0.25, 0.12, 0.15),  # 1 base-right
        (0.3, 0.28, -0.1),  # 2 tip-left
        (0.3, 0.28, 0.1),  # 3 tip-right
    ]
    all_tv = tongue_verts
    tongue_faces: list[Face] = [
        Face(
            vertex_ids=ensure_outward([0, 1, 3, 2], all_tv),
            uvs=project_uv([0, 1, 3, 2], all_tv, _tile(5, 4)),
            color=1,
            dbl=True,
        )
    ]
    tongue_mesh = Mesh(name="tongue", vertices=_flat(tongue_verts), faces=tongue_faces)
    child_nodes.append(
        Node(
            name="tongue",
            mesh=tongue_mesh,
            transform=Transform(pos=(0.0, 0.0, 0.0)),
        )
    )

    # =============================================================== SWOOSH
    # A stylised brand swoosh/stripe on the left side as a dbl=true surface
    swoosh_verts: list[Vec3] = [
        (0.6, -0.28, -0.29),  # 0 toe-point
        (0.3, -0.2, -0.33),  # 1 mid
        (-0.3, 0.05, -0.27),  # 2 curve-top
        (-0.6, 0.0, -0.25),  # 3 heel-point
        (0.5, -0.35, -0.31),  # 4 toe-bottom
        (0.1, -0.3, -0.335),  # 5 mid-bottom
    ]
    all_sw = swoosh_verts
    swoosh_faces: list[Face] = [
        Face(
            vertex_ids=ensure_outward([0, 4, 5, 1, 2, 3], all_sw),
            uvs=project_uv([0, 4, 5, 1, 2, 3], all_sw, _tile_span(5, 5, 1, 2)),
            color=1,
            dbl=True,
        )
    ]
    swoosh_mesh = Mesh(name="swoosh", vertices=_flat(swoosh_verts), faces=swoosh_faces)
    child_nodes.append(
        Node(
            name="swoosh",
            mesh=swoosh_mesh,
            transform=Transform(pos=(0.0, 0.0, 0.0)),
        )
    )

    # =============================================================== SCENE
    shoe_folder = Node(name="shoe", children=child_nodes)
    root = Node(name="root", children=[shoe_folder])

    # =========================================================== TEXTURE
    tex = Texture(background_color=1)

    # --- Sole plate (bottom + top fan triangles) ---
    tex.paint_tile(_tile_span(0, 0, 4, 2), 6)
    # Grip lines on sole bottom
    for row_px in range(0, 32, 4):
        for px in range(7, 57):
            tex.set_pixel(px, row_px, 11)
            tex.set_pixel(px, row_px + 1, 11)

    # --- Sole side walls ---
    tex.paint_tile(_tile(0, 4), 11)  # left-heel-mid
    tex.paint_tile(_tile(0, 5), 11)  # left-mid-toe
    tex.paint_tile(_tile(0, 6), 11)  # right-toe-mid
    tex.paint_tile(_tile(0, 7), 11)  # right-mid-heel
    tex.paint_tile(_tile(1, 4), 11)  # heel-back

    # --- Sole toe front ---
    tex.paint_tile(_tile_span(6, 0, 1, 2), 7)

    # --- Upper left walls ---
    tex.paint_tile(_tile_span(1, 0, 2, 2), 2)
    tex.paint_tile(_tile_span(1, 2, 2, 2), 2)
    # White brand stripe on left side
    for px in range(0, 16):
        tex.set_pixel(8 + px, 16 + 12, 1)
        tex.set_pixel(8 + px, 16 + 13, 1)

    # --- Upper right walls ---
    tex.paint_tile(_tile_span(1, 4, 2, 2), 3)
    tex.paint_tile(_tile_span(1, 6, 2, 2), 3)

    # --- Heel back + counter ---
    tex.paint_tile(_tile(3, 0), 3)
    tex.paint_tile(_tile(3, 1), 2)

    # --- Toe box ---
    tex.paint_tile(_tile_span(3, 2, 1, 2), 4)

    # --- Instep / lace area ---
    tex.paint_tile(_tile_span(3, 3, 1, 2), 1)
    tex.paint_tile(_tile_span(3, 5, 1, 1), 1)
    tex.paint_tile(_tile_span(4, 0, 1, 2), 1)
    # Lace eyelets
    for ly in (8, 16):
        for lx in (6, 12):
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    tex.set_pixel(3 * 16 + lx + dx, 3 * 16 + ly + dy, 0)

    # --- Collar rim ---
    tex.paint_tile(_tile(4, 2), 5)

    # --- Heel counter ---
    tex.paint_tile(_tile(4, 3), 2)
    tex.paint_tile(_tile(4, 4), 3)
    tex.paint_tile(_tile(4, 5), 2)
    tex.paint_tile(_tile(4, 6), 4)

    # --- Upper bottom cap ---
    tex.paint_tile(_tile(5, 7), 5)

    # --- Cleat studs ---
    for i in range(4):
        tex.paint_tile(_tile(5, i), 6)

    # --- Tongue ---
    tex.paint_tile(_tile(5, 4), 1)

    # --- Swoosh ---
    tex.paint_tile(_tile_span(5, 5, 1, 2), 1)

    # --- Brand accent on heel counter tile ---
    for px in range(8):
        tex.set_pixel(4 * 16 + 4 + px, 5 * 16 + 8, 12)
        tex.set_pixel(4 * 16 + 4 + px, 5 * 16 + 9, 12)

    return Model(
        root=root,
        texture=tex,
        colors=FOOTBALL_SHOE_COLORS,
        shade_pal_1=FOOTBALL_SHOE_SHADE_PAL_1,
        shade_pal_2=FOOTBALL_SHOE_SHADE_PAL_2,
        background_color=1,
        transparent_color=14,
        shading_mode=1,
        motion_duration=2,
        camera=Camera(
            pos=(3.0, 1.5, 3.5),
            target=(0.0, -0.1, 0.0),
            distance_to_target=5.0,
            omega=-0.8,
            theta=0.35,
        ),
    )


def main() -> None:
    """Write ``models/football_shoe/<name>.txt``."""
    model = build_football_shoe()
    script_name = Path(__file__).resolve().name
    model_name = script_name.removeprefix("gen_").replace(".py", ".txt")
    out_path = (
        Path(__file__).resolve().parent.parent.parent / "models" / "football_shoe" / model_name
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.write(out_path)
    print(f"wrote {out_path}")
    total_verts = 0
    total_faces = 0

    def _count(node: Node) -> None:
        nonlocal total_verts, total_faces
        if node.mesh is not None:
            total_verts += len(node.mesh.vertices) // 3
            total_faces += len(node.mesh.faces)
        for child in node.children:
            _count(child)

    _count(model.root)
    print(f"verts={total_verts} faces={total_faces}")
    print("parts: sole, upper, heel_counter, 6x cleats, tongue, swoosh")


if __name__ == "__main__":
    main()
