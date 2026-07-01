"""Recipe: low-poly blue+white football boot for picoCAD 2.

A stylised soccer cleat with:

* blue synthetic-fibre upper, white lateral three-stripe brand mark
* white instep / laces with five criss-crossing strips and a tongue flap
* raised heel counter and rounded toe box
* grey sole plate with eight conical studs and a darker grip pattern
* 16-color palette (blue / white / silver) on a dark "pitch" background
  that contrasts with the white sole and laces

The boot is oriented with +X = toe, -X = heel, +Y = up, +Z = right (lateral)
side, -Z = left (medial) side. Mirroring the recipe to swap lateral / medial
is a one-line change if a left-foot variant is wanted later.

Run::

    uv run python scripts/gen_football_boot.py
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from picocad.model import Camera, Face, Mesh, Model, Node
from picocad.texture import Texture
from picocad.uv import project_uv


def ensure_outward_dir(
    vids: Sequence[int],
    all_verts: Sequence[Vec3],
    expected_dir: Vec3,
) -> list[int]:
    """Ensure the polygon winds so picoCAD's face-culling agrees with us.

    picoCAD's PS1-style rasteriser treats the face normal as the
    cross-product of its first three vertices, then back-face-culls by
    that normal. The toolkit's :func:`picocad.uv.ensure_outward` (and our
    earlier Newell-based variant) silently fail for thin parts that sit
    off-origin (such as the sole plate at ``y = -0.4``) and for n-gons
    where the first three vertices are nearly co-linear with the face
    plane's "weak" axis (such as the 5-gon toe cap and 6-gon toe front
    -- both spanned across the y axis so the first three vertices form
    a near-horizontal triangle whose normal is mostly +Y, not +X).

    The fix: compute the normal as the cross product of the first three
    vertices -- exactly what picoCAD does at draw time -- and check its
    alignment with ``expected_dir``. If the cross-product normal points
    the wrong way, the order is reversed (which flips the cross product
    sign while keeping the polygon simple).
    """
    if len(vids) < 3:
        return list(vids)
    a = all_verts[vids[0]]
    b = all_verts[vids[1]]
    c = all_verts[vids[2]]
    e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    n_vec = (
        e1[1] * e2[2] - e1[2] * e2[1],
        e1[2] * e2[0] - e1[0] * e2[2],
        e1[0] * e2[1] - e1[1] * e2[0],
    )
    dot = n_vec[0] * expected_dir[0] + n_vec[1] * expected_dir[1] + n_vec[2] * expected_dir[2]
    if dot < 0.0:
        return list(reversed(vids))
    return list(vids)


if TYPE_CHECKING:
    from collections.abc import Sequence

Vec3 = tuple[float, float, float]

# 8x8 grid of 16x16 px tiles on the 128x128 texture.
TILE: float = 0.125


def _tile(row: int, col: int) -> tuple[float, float, float, float]:
    """Return the UV rect for a single 16x16 tile at (row, col)."""
    return (col * TILE, row * TILE, (col + 1) * TILE, (row + 1) * TILE)


def _tile_span(row: int, col: int, w: int, h: int) -> tuple[float, float, float, float]:
    """Return the UV rect spanning ``w`` columns and ``h`` rows at (row, col)."""
    return (col * TILE, row * TILE, (col + w) * TILE, (row + h) * TILE)


def _flat(verts: Sequence[Vec3]) -> list[float]:
    """Flatten a list of Vec3 tuples into a flat [x,y,z, x,y,z, ...] list."""
    out: list[float] = []
    for v in verts:
        out.extend(v)
    return out


# --------------------------------------------------------------------- palette
# 16-color palette: blue/white/silver football boot on a dark pitch background.
# Slot 9 = dark green (background_color); slot 14 = transparent (reserved).
BOOT_COLORS: list[Vec3] = [
    (0.00, 0.00, 0.00),  #  0 black (lace holes, brand mark, outlines)
    (0.98, 0.98, 0.98),  #  1 white (sole, laces, three-stripe, tongue)
    (0.18, 0.42, 0.80),  #  2 royal blue (main upper)
    (0.08, 0.22, 0.52),  #  3 dark blue (shaded upper)
    (0.35, 0.58, 0.92),  #  4 light blue (lit upper, toe cap)
    (0.03, 0.10, 0.28),  #  5 navy (heel counter, deep shadow)
    (0.78, 0.80, 0.84),  #  6 silver (sole plate top)
    (0.45, 0.48, 0.52),  #  7 dark silver (sole sides, stud body)
    (0.90, 0.92, 0.94),  #  8 light silver (stud highlight)
    (0.13, 0.30, 0.13),  #  9 dark green (BACKGROUND = football pitch)
    (0.30, 0.32, 0.35),  # 10 charcoal (sole bottom grip lines)
    (0.55, 0.72, 0.96),  # 11 pale blue (sky-highlight on collar rim)
    (0.04, 0.14, 0.38),  # 12 deep blue (heel back panel)
    (0.94, 0.95, 0.96),  # 13 off-white (lace texture)
    (1.00, 1.00, 1.00),  # 14 transparent (reserved)
    (0.62, 0.66, 0.70),  # 15 mid silver (sole side wall)
]

# Lit-side ramp: lift each base colour toward its lit variant.
BOOT_SHADE_PAL_1: list[int] = [
    0,  #  0 black -> black
    13,  #  1 white -> off-white (already bright)
    4,  #  2 royal blue -> light blue
    2,  #  3 dark blue -> royal blue
    4,  #  4 light blue -> light blue
    3,  #  5 navy -> dark blue
    8,  #  6 silver -> light silver
    6,  #  7 dark silver -> silver
    8,  #  8 light silver -> light silver
    9,  #  9 dark green -> dark green (no remap)
    7,  # 10 charcoal -> dark silver
    4,  # 11 pale blue -> light blue
    3,  # 12 deep blue -> dark blue
    1,  # 13 off-white -> white
    14,  # 14 transparent
    6,  # 15 mid silver -> silver
]

# Shadow-side ramp: drop each base colour toward its shaded variant.
BOOT_SHADE_PAL_2: list[int] = [
    0,  #  0 black -> black
    15,  #  1 white -> mid silver (ambient reads as cool grey)
    3,  #  2 royal blue -> dark blue
    5,  #  3 dark blue -> navy
    2,  #  4 light blue -> royal blue
    0,  #  5 navy -> black
    7,  #  6 silver -> dark silver
    10,  #  7 dark silver -> charcoal
    6,  #  8 light silver -> silver
    9,  #  9 dark green -> dark green (no remap)
    0,  # 10 charcoal -> black
    3,  # 11 pale blue -> dark blue
    5,  # 12 deep blue -> navy
    9,  # 13 off-white -> dark green (deep shadow on laces)
    14,  # 14 transparent
    7,  # 15 mid silver -> dark silver
]


# ============================================================== build pieces
def build_sole() -> Node:
    """Sole plate node: 6-vert top ring + 6-vert bottom ring + 2 toe tips."""
    top: list[Vec3] = [  # 0..5
        (-1.00, -0.40, -0.22),  #  0 heel-left
        (-0.30, -0.40, -0.34),  #  1 mid-left
        (0.40, -0.38, -0.28),  #  2 fore-left
        (0.40, -0.38, 0.28),  #  3 fore-right
        (-0.30, -0.40, 0.34),  #  4 mid-right
        (-1.00, -0.40, 0.22),  #  5 heel-right
    ]
    bot: list[Vec3] = [  # 6..11
        (-1.00, -0.55, -0.22),  #  6 heel-left-bottom
        (-0.30, -0.55, -0.34),  #  7 mid-left-bottom
        (0.40, -0.55, -0.28),  #  8 fore-left-bottom
        (0.40, -0.55, 0.28),  #  9 fore-right-bottom
        (-0.30, -0.55, 0.34),  # 10 mid-right-bottom
        (-1.00, -0.55, 0.22),  # 11 heel-right-bottom
    ]
    tip_top: Vec3 = (0.92, -0.36, 0.0)  # 12
    tip_bot: Vec3 = (0.92, -0.54, 0.0)  # 13
    verts = top + bot + [tip_top, tip_bot]
    all_v = verts

    faces: list[Face] = []
    # Sole top (visible only as a thin edge between upper and sole).
    faces.append(
        Face(
            vertex_ids=ensure_outward_dir([12, 2, 1, 0, 5, 4, 3], all_v, (0.0, 1.0, 0.0)),
            uvs=project_uv([12, 2, 1, 0, 5, 4, 3], all_v, _tile_span(0, 0, 4, 1)),
            color=6,
        )
    )
    # Sole bottom: 6 triangles fanning from tip_bot.
    _bot_fan = [
        [13, 6, 7],
        [13, 7, 8],
        [13, 8, 9],
        [13, 9, 10],
        [13, 10, 11],
        [13, 11, 6],
    ]
    for tri in _bot_fan:
        faces.append(
            Face(
                vertex_ids=ensure_outward_dir(tri, all_v, (0.0, -1.0, 0.0)),
                uvs=project_uv(tri, all_v, _tile_span(0, 0, 4, 1)),
                color=10,
            )
        )
    # Sole side wall: 6 quads around the perimeter.
    # Each wall's outward direction is the normalised (x, 0, z) of the
    # quad's centroid. The 6 verts of the top ring are placed at roughly
    # equal angles around the boot, so we can hardcode 6 directions.
    wall_dirs: list[Vec3] = [
        (-0.85, 0.0, -0.53),  # 0: heel-left
        (-0.30, 0.0, -0.95),  # 1: mid-left
        (0.50, 0.0, -0.87),  # 2: fore-left
        (0.50, 0.0, 0.87),  # 3: fore-right
        (-0.30, 0.0, 0.95),  # 4: mid-right
        (-0.85, 0.0, 0.53),  # 5: heel-right
    ]
    for i in range(6):
        j = (i + 1) % 6
        quad = [i, j, j + 6, i + 6]
        faces.append(
            Face(
                vertex_ids=ensure_outward_dir(quad, all_v, wall_dirs[i]),
                uvs=project_uv(quad, all_v, _tile(0, 4 + (i % 2) * 2)),
                color=15,
            )
        )
    # Sole toe front (6-gon between top-tip and bottom-tip).
    # Note: the 6-gon is "vertical" (spans y from -0.36 to -0.55), so any
    # naive (12, 2, 3, ...) ordering has its first 3 verts forming a
    # near-horizontal triangle whose cross product is mostly +Y -- picoCAD
    # would then cull the face from a head-on +X view. We start the loop
    # at the top-tip, jump to the bottom-tip (so the first 3 verts include
    # a Y-spanning edge), then walk the bottom and top rings back to the
    # start. This is still a simple polygon (uses the same 6 edges) but
    # its first 3 verts form a triangle that is in the YZ plane and
    # therefore gives a +X cross product.
    faces.append(
        Face(
            vertex_ids=ensure_outward_dir([12, 13, 8, 9, 3, 2], all_v, (1.0, 0.0, 0.0)),
            uvs=project_uv([12, 13, 8, 9, 3, 2], all_v, _tile(0, 5)),
            color=7,
        )
    )

    return Node(
        name="sole",
        mesh=Mesh(name="sole", vertices=_flat(verts), faces=faces),
    )


def build_upper() -> Node:
    """Upper body: 3 rings of 6 verts (bottom / mid / collar) + toe tip."""
    bot: list[Vec3] = [  # 0..5 — same footprint as sole top
        (-1.00, -0.40, -0.20),  #  0 heel-left
        (-0.30, -0.40, -0.30),  #  1 mid-left
        (0.40, -0.38, -0.26),  #  2 fore-left
        (0.40, -0.38, 0.26),  #  3 fore-right
        (-0.30, -0.40, 0.30),  #  4 mid-right
        (-1.00, -0.40, 0.20),  #  5 heel-right
    ]
    mid: list[Vec3] = [  # 6..11
        (-1.00, 0.00, -0.18),  #  6
        (-0.30, 0.00, -0.26),  #  7
        (0.40, 0.02, -0.22),  #  8
        (0.40, 0.02, 0.22),  #  9
        (-0.30, 0.00, 0.26),  # 10
        (-1.00, 0.00, 0.18),  # 11
    ]
    col: list[Vec3] = [  # 12..17 — collar, heel taller, toe lower
        (-1.00, 0.20, -0.15),  # 12
        (-0.40, 0.16, -0.22),  # 13
        (0.20, 0.12, -0.18),  # 14
        (0.20, 0.12, 0.18),  # 15
        (-0.40, 0.16, 0.22),  # 16
        (-1.00, 0.20, 0.15),  # 17
    ]
    toe_tip: Vec3 = (0.85, -0.22, 0.0)  # 18
    verts = bot + mid + col + [toe_tip]
    all_v = verts

    faces: list[Face] = []
    # Lower wall: 6 quads bottom -> mid.
    # Tile allocation: lateral (right, +Z) walls get row-1 cols 0..2 so the
    # brand-stripe pattern is painted into the same tiles the faces use;
    # medial (left, -Z) walls get row-2 cols 0..2.
    for i in range(6):
        j = (i + 1) % 6
        # Lateral (right, +Z) side: royal blue. Medial (left, -Z): dark blue.
        color = 2 if i in (3, 4, 5) else 3
        # Outward direction is the (x, z) component of the wall midpoint.
        mid_x = (all_v[i][0] + all_v[j][0]) / 2
        mid_z = (all_v[i][2] + all_v[j][2]) / 2
        out_dir: Vec3 = (mid_x, 0.0, mid_z)
        # Lateral i=3,4,5 map to row 1 cols 0,1,2 (with the brand stripes);
        # medial i=0,1,2 map to row 2 cols 0,1,2.
        if i in (3, 4, 5):
            tile_col = i - 3  # 3->0, 4->1, 5->2
            tile = _tile(1, tile_col)
        else:
            tile_col = i  # 0->0, 1->1, 2->2
            tile = _tile(2, tile_col)
        faces.append(
            Face(
                vertex_ids=ensure_outward_dir([i, j, j + 6, i + 6], all_v, out_dir),
                uvs=project_uv([i, j, j + 6, i + 6], all_v, tile),
                color=color,
            )
        )
    # Upper wall: 6 quads mid -> collar. Tiles row 1/2 cols 3..5.
    for i in range(6):
        j = (i + 1) % 6
        color = 2 if i in (3, 4, 5) else 3
        mid_x = (all_v[i + 6][0] + all_v[j + 6][0]) / 2
        mid_z = (all_v[i + 6][2] + all_v[j + 6][2]) / 2
        out_dir = (mid_x, 0.0, mid_z)
        if i in (3, 4, 5):
            tile_col = 3 + (i - 3)  # 3->3, 4->4, 5->5
            tile = _tile(1, tile_col)
        else:
            tile_col = 3 + i  # 0->3, 1->4, 2->5
            tile = _tile(2, tile_col)
        faces.append(
            Face(
                vertex_ids=ensure_outward_dir([i + 6, j + 6, j + 12, i + 12], all_v, out_dir),
                uvs=project_uv([i + 6, j + 6, j + 12, i + 12], all_v, tile),
                color=color,
            )
        )

    # Toe cap (5-gon) — light blue, raised toe. Faces +X.
    faces.append(
        Face(
            vertex_ids=ensure_outward_dir([2, 3, 9, 8, 18], all_v, (1.0, 0.0, 0.0)),
            uvs=project_uv([2, 3, 9, 8, 18], all_v, _tile(3, 0)),
            color=4,
        )
    )
    # Toe front (4-gon between toe_tip and toe vertices). Faces +X.
    faces.append(
        Face(
            vertex_ids=ensure_outward_dir([2, 18, 3], all_v, (1.0, 0.0, 0.0)),
            uvs=project_uv([2, 18, 3], all_v, _tile(3, 1)),
            color=4,
        )
    )

    # Heel back panel (4-gon). Faces -X.
    faces.append(
        Face(
            vertex_ids=ensure_outward_dir([5, 0, 6, 11], all_v, (-1.0, 0.0, 0.0)),
            uvs=project_uv([5, 0, 6, 11], all_v, _tile(3, 2)),
            color=12,
        )
    )
    # Heel back upper (4-gon) — connects mid to collar at the back. Faces -X.
    faces.append(
        Face(
            vertex_ids=ensure_outward_dir([11, 6, 12, 17], all_v, (-1.0, 0.0, 0.0)),
            uvs=project_uv([11, 6, 12, 17], all_v, _tile(3, 3)),
            color=12,
        )
    )

    # Collar rim: 6-gon around the top opening (double-sided so it reads
    # from above and below). Faces +Y.
    faces.append(
        Face(
            vertex_ids=ensure_outward_dir([12, 13, 14, 15, 16, 17], all_v, (0.0, 1.0, 0.0)),
            uvs=project_uv([12, 13, 14, 15, 16, 17], all_v, _tile(3, 5)),
            color=11,
            dbl=True,
        )
    )

    return Node(
        name="upper",
        mesh=Mesh(name="upper", vertices=_flat(verts), faces=faces),
    )


def build_tongue() -> Node:
    """Tongue flap: a flat double-sided quad that sits inside the lace deck."""
    verts: list[Vec3] = [
        (-0.10, 0.20, -0.10),  #  0 base-left
        (-0.10, 0.20, 0.10),  #  1 base-right
        (0.30, 0.32, -0.06),  #  2 tip-left
        (0.30, 0.32, 0.06),  #  3 tip-right
    ]
    all_v = verts
    faces: list[Face] = [
        Face(
            vertex_ids=ensure_outward_dir([0, 1, 3, 2], all_v, (0.0, 1.0, 0.0)),
            uvs=project_uv([0, 1, 3, 2], all_v, _tile(4, 0)),
            color=1,
            dbl=True,
        )
    ]
    return Node(
        name="tongue",
        mesh=Mesh(name="tongue", vertices=_flat(verts), faces=faces),
    )


def build_laces() -> Node:
    """Criss-cross lace strips laid over the tongue area.

    Four horizontal "rungs" alternating with three diagonal cross-strips
    form the typical shoe-lace pattern. All strips are very thin so the
    tongue underneath stays visible. ``dbl=True`` keeps the strips
    visible from both above and below the lace deck.
    """
    laces: list[tuple[Vec3, Vec3, Vec3, Vec3]] = []
    z_strip = -0.09
    z_strip_r = 0.09
    y_top = 0.245  # a hair above the upper's collar plane (y = 0.16..0.20)
    y_cross = 0.255  # cross strips sit slightly higher to suggest weaving

    # Four horizontal rungs spaced across the lace area (heel -> toe).
    for k in range(4):
        x0 = -0.30 + k * 0.18
        x1 = x0 + 0.14
        laces.append(
            (
                (x0, y_top, z_strip),
                (x1, y_top, z_strip),
                (x1, y_top, z_strip_r),
                (x0, y_top, z_strip_r),
            )
        )

    # Three diagonal cross-strips. Each one spans the same x range as two
    # adjacent rungs, sloping in the opposite direction.
    for k in range(3):
        x0 = -0.20 + k * 0.18
        x1 = x0 + 0.18
        laces.append(
            (
                (x0, y_cross, z_strip),
                (x1, y_cross, z_strip),
                (x1, y_cross, z_strip_r),
                (x0, y_cross, z_strip_r),
            )
        )

    nodes: list[Node] = []
    for idx, quad in enumerate(laces):
        u0 = 0.4 + idx * 0.05
        v0 = 0.65
        tile = (u0, v0, u0 + 0.05, v0 + 0.06)
        faces: list[Face] = [
            Face(
                vertex_ids=ensure_outward_dir([0, 1, 2, 3], quad, (0.0, 1.0, 0.0)),
                uvs=project_uv([0, 1, 2, 3], quad, tile),
                color=1,
                dbl=True,
            )
        ]
        nodes.append(
            Node(
                name=f"lace_{idx}",
                mesh=Mesh(name=f"lace_{idx}", vertices=_flat(quad), faces=faces),
            )
        )
    return Node(name="laces", children=nodes)


def build_studs() -> Node:
    """Six small conical studs under the sole plate."""
    # (x, y_base, z) positions for the 6 studs.
    positions: list[Vec3] = [
        (-0.85, -0.55, 0.00),  # heel
        (-0.40, -0.55, -0.22),  # mid-left
        (-0.40, -0.55, 0.22),  # mid-right
        (0.15, -0.55, -0.18),  # fore-left
        (0.15, -0.55, 0.18),  # fore-right
        (0.60, -0.55, 0.00),  # toe
    ]
    nodes: list[Node] = []
    for idx, base in enumerate(positions):
        bx, by, bz = base
        r = 0.05
        h = 0.10
        verts: list[Vec3] = [
            (bx - r, by, bz - r),  # 0
            (bx + r, by, bz - r),  # 1
            (bx + r, by, bz + r),  # 2
            (bx - r, by, bz + r),  # 3
            (bx, by - h, bz),  # 4 tip
        ]
        all_v = verts
        # 4 side triangles; alternate tile colors for subtle variation.
        faces: list[Face] = []
        for k in range(4):
            tri = [k, (k + 1) % 4, 4]
            # Triangle's outward direction is the base midpoint's (x,z) dir.
            base_mid_x = (all_v[k][0] + all_v[(k + 1) % 4][0]) / 2 - bx
            base_mid_z = (all_v[k][2] + all_v[(k + 1) % 4][2]) / 2 - bz
            out_dir = (base_mid_x, -1.0, base_mid_z)
            tile_col = 6 + (k % 2)  # alternate silver / light silver
            faces.append(
                Face(
                    vertex_ids=ensure_outward_dir(tri, all_v, out_dir),
                    uvs=project_uv(tri, all_v, _tile(5, idx % 4)),
                    color=tile_col,
                )
            )
        nodes.append(
            Node(
                name=f"stud_{idx}",
                mesh=Mesh(name=f"stud_{idx}", vertices=_flat(verts), faces=faces),
            )
        )
    return Node(name="studs", children=nodes)


def build_brand_stripes() -> Node:
    """Three white 'Adidas-style' stripes painted on the lateral side of the upper.

    Each stripe is a thin flat quad raised slightly off the upper surface so
    it reads as a separate decal. The stripes angle back from toe to heel,
    like real football boot branding.
    """
    stripes: list[tuple[Vec3, Vec3, Vec3, Vec3]] = []
    # Place stripes just outside the lateral wall (z ~ 0.30 at mid-height)
    # so they read as decals painted on the side, not embedded in the body.
    z_centers = [0.31, 0.35, 0.39]
    y_base = -0.10
    y_top = 0.05
    for zc in z_centers:
        x0 = -0.25
        x1 = 0.30
        z0 = zc - 0.012
        z1 = zc + 0.012
        stripes.append(
            (
                (x0, y_base, z0),
                (x1, y_base, z0),
                (x1, y_top, z1),
                (x0, y_top, z1),
            )
        )

    nodes: list[Node] = []
    for idx, quad in enumerate(stripes):
        tile = _tile(4, 1 + idx)
        # Stripes are painted on the lateral (+Z) side of the upper, so
        # they should face +Z, not +Y. The slight Y slope of the stripe
        # (y_base=-0.10 -> y_top=+0.05) makes the first-3-verts cross
        # product lean -Y by a tiny amount, but +Z is the dominant
        # component, so expected_dir = (0, 0, 1) keeps the order
        # un-reversed (i.e. the stripe faces outward, not into the boot).
        faces: list[Face] = [
            Face(
                vertex_ids=ensure_outward_dir([0, 1, 2, 3], quad, (0.0, 0.0, 1.0)),
                uvs=project_uv([0, 1, 2, 3], quad, tile),
                color=1,
            )
        ]
        nodes.append(
            Node(
                name=f"stripe_{idx}",
                mesh=Mesh(name=f"stripe_{idx}", vertices=_flat(quad), faces=faces),
            )
        )
    return Node(name="stripes", children=nodes)


def build_brand_mark() -> Node:
    """A small dark brand mark on the tongue (a simple diamond / lozenge)."""
    verts: list[Vec3] = [
        (0.10, 0.27, -0.04),  # 0 back
        (0.20, 0.27, 0.0),  # 1 right
        (0.10, 0.27, 0.04),  # 2 front
        (0.00, 0.27, 0.0),  # 3 left
    ]
    all_v = verts
    faces: list[Face] = [
        Face(
            vertex_ids=ensure_outward_dir([0, 1, 2, 3], all_v, (0.0, 1.0, 0.0)),
            uvs=project_uv([0, 1, 2, 3], all_v, _tile(4, 5)),
            color=0,
            dbl=True,
        )
    ]
    return Node(
        name="brand_mark",
        mesh=Mesh(name="brand_mark", vertices=_flat(verts), faces=faces),
    )


def build_heel_counter() -> Node:
    """A small raised heel counter at the back of the boot.

    Real football boots have a reinforced heel counter (a slightly raised
    cup at the back) for ankle support. Modeled here as a small box
    attached to the back of the upper.
    """
    verts: list[Vec3] = [
        (-1.00, 0.18, -0.15),  # 0 base-left (matches upper collar)
        (-1.00, 0.18, 0.15),  # 1 base-right
        (-1.00, 0.00, -0.18),  # 2 mid-left
        (-1.00, 0.00, 0.18),  # 3 mid-right
        (-1.10, 0.10, -0.10),  # 4 top-left (raised)
        (-1.10, 0.10, 0.10),  # 5 top-right (raised)
    ]
    all_v = verts
    faces: list[Face] = []
    # Back face (-X).
    faces.append(
        Face(
            vertex_ids=ensure_outward_dir([0, 1, 5, 4], all_v, (-1.0, 0.0, 0.0)),
            uvs=project_uv([0, 1, 5, 4], all_v, _tile(3, 6)),
            color=5,
        )
    )
    # Side faces.
    faces.append(
        Face(
            vertex_ids=ensure_outward_dir([0, 4, 2], all_v, (0.0, 0.0, -1.0)),
            uvs=project_uv([0, 4, 2], all_v, _tile(3, 7)),
            color=5,
        )
    )
    faces.append(
        Face(
            vertex_ids=ensure_outward_dir([1, 3, 5], all_v, (0.0, 0.0, 1.0)),
            uvs=project_uv([1, 3, 5], all_v, _tile(3, 7)),
            color=5,
        )
    )
    # Top face (+Y).
    faces.append(
        Face(
            vertex_ids=ensure_outward_dir([4, 5, 3, 2], all_v, (0.0, 1.0, 0.0)),
            uvs=project_uv([4, 5, 3, 2], all_v, _tile(3, 7)),
            color=5,
        )
    )
    return Node(
        name="heel_counter",
        mesh=Mesh(name="heel_counter", vertices=_flat(verts), faces=faces),
    )


# ============================================================== texture paint
def _paint_solid(tex: Texture, tile: tuple[float, float, float, float], color: int) -> None:
    """Flood-fill a tile with ``color``."""
    tex.paint_tile(tile, color)


def _paint_pixel(
    tex: Texture,
    u: float,
    v: float,
    color: int,
) -> None:
    """Set a single pixel at UV ``(u, v)`` in [0, 1] space."""
    x = int(u * 128)
    y = int(v * 128)
    if 0 <= x < 128 and 0 <= y < 128:
        tex.set_pixel(x, y, color)


def _paint_brand_stripes(tex: Texture) -> None:
    """Paint three white Adidas-style stripes on the lateral upper tiles.

    The lateral lower walls use row 1, cols 0..2. We paint three diagonal
    stripes that run from heel to toe inside each tile, evoking the
    Adidas three-stripe trademark.
    """
    for col in range(3):
        u0 = col * TILE
        v0 = 1 * TILE  # row 1
        # Three diagonal stripes per tile.
        for k in range(3):
            offset = 0.02 + k * 0.04
            for t in range(8):
                u = u0 + 0.02 + t * (TILE - 0.04) / 8
                v = v0 + offset
                if u < u0 + TILE - 0.01 and v < v0 + TILE - 0.01:
                    _paint_pixel(tex, u, v, 1)
                    _paint_pixel(tex, u, v + 0.005, 1)


def _paint_sole_grip(tex: Texture) -> None:
    """Paint a darker grip pattern on the sole-bottom tile (row 0)."""
    # Sole bottom covers tile (0, 0)-(0, 4) wide, but only 1 tile tall. We
    # used the 0..3 columns for sole top, so let me redo: sole bottom uses
    # the 4-wide tile (0,0)-(4*TILE, TILE). Add grip dots.
    u0 = 0.0
    v0 = 0.0
    # Several grip dots in a pattern.
    for ix in range(4):
        for iy in range(2):
            cx = u0 + (ix + 0.5) * TILE / 2 + 0.005
            cy = v0 + (iy + 0.5) * TILE / 2 + 0.005
            # 2x2 dot
            for dx in range(2):
                for dy in range(2):
                    _paint_pixel(tex, cx + dx * 0.005, cy + dy * 0.005, 10)


def _paint_studs(tex: Texture) -> None:
    """Add a small light highlight to each stud's tile at row 5, col 0..3."""
    for col in range(4):
        u0 = col * TILE
        v0 = 5 * TILE
        # Small highlight at the top-left of each tile.
        for dx in range(2):
            for dy in range(2):
                _paint_pixel(tex, u0 + 0.02 + dx * 0.005, v0 + 0.02 + dy * 0.005, 8)


def _paint_eyelet_holes(tex: Texture) -> None:
    """Paint a few black eyelet holes on the lace area tiles.

    The tongue tile is at (4, 0); the lace strips use the right half of row 4
    and the row 0..0.5 of the right side. Place a few black pixels in the
    tongue tile to suggest eyelet holes.
    """
    # Tongue tile: (4, 0) — 1 tile in row 4, col 0.
    cx = 4 * TILE + TILE / 2
    cy = 4 * TILE + TILE / 2
    for i in range(5):
        ey = cy + (i - 2) * 0.025
        # left eyelet
        _paint_pixel(tex, cx - 0.03, ey, 0)
        _paint_pixel(tex, cx - 0.029, ey, 0)
        # right eyelet
        _paint_pixel(tex, cx + 0.03, ey, 0)
        _paint_pixel(tex, cx + 0.031, ey, 0)


def _paint_brand_mark(tex: Texture) -> None:
    """Paint a small dark diamond on the tongue tile (row 4, col 5)."""
    cx = 5 * TILE + TILE / 2
    cy = 4 * TILE + TILE / 2
    # Small diamond shape
    for d in range(4):
        _paint_pixel(tex, cx + d * 0.01, cy, 0)
        _paint_pixel(tex, cx - d * 0.01, cy, 0)
        _paint_pixel(tex, cx, cy + d * 0.01, 0)
        _paint_pixel(tex, cx, cy - d * 0.01, 0)


def _paint_stripes_decoration(tex: Texture) -> None:
    """Re-paint the lateral-side upper tiles with stripes overlay.

    The brand stripes are 3D meshes (separate small quads), so we don't need
    to paint stripes into the texture. This function is a no-op kept for
    future use when stitching a 2D pattern into the upper.
    """


def _paint_all(tex: Texture) -> None:
    """Paint the full 128x128 texture with all detail passes."""
    # ------------------------------------------------------------------ ROW 0
    # Sole: cols 0..3 = sole top (silver w/ grip), cols 4..7 = sole side walls
    # and toe-front face.
    _paint_solid(tex, _tile_span(0, 0, 4, 1), 6)
    _paint_sole_grip(tex)
    _paint_solid(tex, _tile(0, 4), 15)
    _paint_solid(tex, _tile(0, 5), 7)  # toe-front tile (dark silver)
    _paint_solid(tex, _tile(0, 6), 15)
    _paint_solid(tex, _tile(0, 7), 15)

    # ------------------------------------------------------------------ ROW 1
    # Lateral walls: cols 0..2 = lower wall (royal blue w/ 3 white stripes);
    # cols 3..5 = upper wall (royal blue). Cols 6..7 left to TOE_FRONT triangle
    # (col 6) and the unused gap (col 7). The TOE_CAP pentagon uses
    # _tile(3, 0) instead, so col 7 is just a green background.
    for col in range(3):
        _paint_solid(tex, _tile(1, col), 2)
    _paint_brand_stripes(tex)
    for col in range(3, 6):
        _paint_solid(tex, _tile(1, col), 2)
    # Col 6 is unused by the upper; col 7 is also unused.

    # ------------------------------------------------------------------ ROW 2
    # Medial walls: cols 0..2 = lower wall (dark blue), cols 3..5 = upper wall.
    for col in range(3):
        _paint_solid(tex, _tile(2, col), 3)
    for col in range(3, 6):
        _paint_solid(tex, _tile(2, col), 3)
    # Cols 6..7 unused by the upper.

    # ------------------------------------------------------------------ ROW 3
    # Toe cap, toe front, heel back, collar rim.
    _paint_solid(tex, _tile(3, 0), 4)  # toe cap
    _paint_solid(tex, _tile(3, 1), 4)  # toe front triangle
    _paint_solid(tex, _tile(3, 2), 12)  # heel back lower (deep blue)
    _paint_solid(tex, _tile(3, 3), 12)  # heel back upper (deep blue)
    _paint_solid(tex, _tile(3, 4), 12)  # spare (matches heel for symmetry)
    _paint_solid(tex, _tile(3, 5), 11)  # collar rim (pale blue highlight)
    _paint_solid(tex, _tile(3, 6), 5)  # spare
    _paint_solid(tex, _tile(3, 7), 5)  # spare

    # ------------------------------------------------------------------ ROW 4
    # Tongue, brand mark, and lace tiles.
    _paint_solid(tex, _tile(4, 0), 1)  # tongue base
    _paint_solid(tex, _tile(4, 1), 1)  # spare (was 3D-stripe decal)
    _paint_solid(tex, _tile(4, 2), 1)
    _paint_solid(tex, _tile(4, 3), 1)
    _paint_solid(tex, _tile(4, 4), 1)
    _paint_solid(tex, _tile(4, 5), 1)  # brand mark base
    _paint_solid(tex, _tile(4, 6), 1)  # spare
    _paint_solid(tex, _tile(4, 7), 1)  # spare
    _paint_eyelet_holes(tex)
    _paint_brand_mark(tex)

    # ------------------------------------------------------------------ ROW 5
    # Studs (6 of them, but the tile grid only has 4 cols available since the
    # other 4 are used elsewhere). Studs share tiles 0..3.
    for col in range(4):
        _paint_solid(tex, _tile(5, col), 7)
    _paint_studs(tex)

    # ------------------------------------------------------------------ ROWS 6..7
    # Left as background (dark green pitch).


# ============================================================== model entry
def build_football_boot() -> Model:
    """Assemble the full football boot model."""
    sole = build_sole()
    upper = build_upper()
    tongue = build_tongue()
    laces = build_laces()
    studs = build_studs()
    stripes = build_brand_stripes()
    brand = build_brand_mark()
    heel = build_heel_counter()

    # Group: root -> boot -> {sole, upper, ...}
    boot_group = Node(
        name="boot",
        children=[sole, upper, tongue, laces, studs, stripes, brand, heel],
    )
    root = Node(name="root", children=[boot_group])

    tex = Texture(background_color=9)  # dark green pitch
    _paint_all(tex)

    return Model(
        root=root,
        texture=tex,
        colors=BOOT_COLORS,
        shade_pal_1=BOOT_SHADE_PAL_1,
        shade_pal_2=BOOT_SHADE_PAL_2,
        transparent_color=14,
        background_color=9,
        camera=Camera(
            pos=(2.6, 1.6, 2.8),
            target=(0.0, -0.1, 0.0),
            distance_to_target=4.1,
            omega=-1.35,
            theta=0.45,
        ),
    )


def main() -> None:
    """Write the model to ``models/football_shoe/<name>.txt``."""
    model = build_football_boot()
    script_name = Path(__file__).resolve().name
    model_name = script_name.removeprefix("gen_").replace(".py", ".txt")
    out_path = (
        Path(__file__).resolve().parent.parent.parent / "models" / "football_shoe" / model_name
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.write(out_path)
    print(f"wrote {out_path}")
    flat: dict[str, object] = model.to_json()
    graph = flat["graph"]
    assert isinstance(graph, dict)
    children = graph.get("children", [])
    assert isinstance(children, list)
    mesh_count = sum(1 for c in children if isinstance(c, dict) and "mesh" in c)
    for c in children:
        if isinstance(c, dict):
            for cc in c.get("children", []):
                if isinstance(cc, dict) and "mesh" in cc:
                    mesh_count += 1
    print(f"groups={len(children)} meshes={mesh_count} bg=9(green) trans=14")


if __name__ == "__main__":
    main()
