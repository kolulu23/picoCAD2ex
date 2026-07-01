"""Recipe: build a low-poly baby chick model inspired by pixel art.

Run::

    uv run python scripts/gen_chick.py

Outputs ``models/chick.txt``.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING

from picocad.model import Face, Mesh, Model, Node, Transform
from picocad.texture import Texture
from picocad.uv import ensure_outward, project_uv

if TYPE_CHECKING:
    from collections.abc import Sequence

# Type aliases.
Verts = list[float]
FaceSpec = tuple[list[int], int]  # (vertex_ids, palette color)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def make_uv_sphere(
    radius: float,
    n_lon: int,
    n_lat: int,
    *,
    squash_top: float = 1.0,
    squash_bottom: float = 1.0,
) -> tuple[list[float], list[list[int]]]:
    """Generate a UV sphere centred at the origin.

    Parameters
    ----------
    radius
        Sphere radius.
    n_lon
        Number of longitude segments (around).
    n_lat
        Number of latitude segments (top to bottom, excluding poles).
    squash_top
        Scale factor for the top hemisphere (1.0 = normal).
    squash_bottom
        Scale factor for the bottom hemisphere.

    Returns
    -------
    verts : list[float]
        Flat vertex list [x0,y0,z0, x1,y1,z1, ...].
    rings : list[list[int]]
        Ring indices. rings[0] = [top_pole_idx], rings[-1] = [bottom_pole_idx].
    """
    verts: list[float] = []
    rings: list[list[int]] = []

    # Top pole
    verts.extend([0.0, radius, 0.0])
    rings.append([0])

    # Latitude rings
    for i in range(1, n_lat + 1):
        theta = math.pi * i / n_lat
        # Egg shape: squash top/bottom differently
        r = radius * squash_top if theta < math.pi / 2 else radius * squash_bottom
        ring: list[int] = []
        for j in range(n_lon):
            phi = 2 * math.pi * j / n_lon
            x = r * math.sin(theta) * math.cos(phi)
            y = radius * math.cos(theta)
            z = r * math.sin(theta) * math.sin(phi)
            idx = len(verts) // 3
            verts.extend([x, y, z])
            ring.append(idx)
        rings.append(ring)

    # Bottom pole
    idx = len(verts) // 3
    verts.extend([0.0, -radius, 0.0])
    rings.append([idx])

    return verts, rings


def sphere_faces(rings: list[list[int]], n_lon: int) -> list[list[int]]:
    """Generate quad/tri faces from sphere rings.

    Returns 0-based vertex index lists.
    """
    faces: list[list[int]] = []

    # Top cap: triangles from pole to first ring
    pole = rings[0][0]
    ring1 = rings[1]
    for j in range(n_lon):
        j_next = (j + 1) % n_lon
        faces.append([pole, ring1[j_next], ring1[j]])

    # Middle bands: quads
    for i in range(1, len(rings) - 2):
        ring_a = rings[i]
        ring_b = rings[i + 1]
        for j in range(n_lon):
            j_next = (j + 1) % n_lon
            faces.append([ring_a[j], ring_a[j_next], ring_b[j_next], ring_b[j]])

    # Bottom cap: triangles from last ring to pole
    pole = rings[-1][0]
    ring_last = rings[-2]
    for j in range(n_lon):
        j_next = (j + 1) % n_lon
        faces.append([pole, ring_last[j], ring_last[j_next]])

    return faces


def make_cone(
    base_center: Sequence[float],
    tip: Sequence[float],
    base_radius: float,
    n_segments: int,
) -> tuple[list[float], list[list[int]]]:
    """Generate a cone/conical frustum.

    Returns flat verts and 0-based face index lists.
    """
    verts: list[float] = []
    cx, cy, cz = base_center

    # Compute two perpendicular axes in the base plane
    direction = [tip[0] - cx, tip[1] - cy, tip[2] - cz]
    # Find a reference vector not parallel to direction
    # Use the axis with the smallest absolute component.
    abs_d = [abs(direction[0]), abs(direction[1]), abs(direction[2])]
    if abs_d[0] <= abs_d[1] and abs_d[0] <= abs_d[2]:
        ref = [1.0, 0.0, 0.0]
    elif abs_d[1] <= abs_d[2]:
        ref = [0.0, 1.0, 0.0]
    else:
        ref = [0.0, 0.0, 1.0]
    # Cross product for first axis
    ax1 = [
        direction[1] * ref[2] - direction[2] * ref[1],
        direction[2] * ref[0] - direction[0] * ref[2],
        direction[0] * ref[1] - direction[1] * ref[0],
    ]
    ln = math.sqrt(ax1[0] ** 2 + ax1[1] ** 2 + ax1[2] ** 2)
    ax1 = [1.0, 0.0, 0.0] if ln < 1e-12 else [a / ln for a in ax1]
    # Cross product for second axis
    ax2 = [
        direction[1] * ax1[2] - direction[2] * ax1[1],
        direction[2] * ax1[0] - direction[0] * ax1[2],
        direction[0] * ax1[1] - direction[1] * ax1[0],
    ]
    ln = math.sqrt(ax2[0] ** 2 + ax2[1] ** 2 + ax2[2] ** 2)
    ax2 = [a / ln for a in ax2]

    # Base ring vertices
    base_start = len(verts) // 3
    for i in range(n_segments):
        angle = 2 * math.pi * i / n_segments
        x = cx + base_radius * (ax1[0] * math.cos(angle) + ax2[0] * math.sin(angle))
        y = cy + base_radius * (ax1[1] * math.cos(angle) + ax2[1] * math.sin(angle))
        z = cz + base_radius * (ax1[2] * math.cos(angle) + ax2[2] * math.sin(angle))
        verts.extend([x, y, z])

    # Tip vertex
    tip_idx = len(verts) // 3
    verts.extend(tip)

    # Faces: triangles from base ring to tip
    faces: list[list[int]] = []
    for i in range(n_segments):
        i_next = (i + 1) % n_segments
        faces.append([base_start + i, base_start + i_next, tip_idx])

    return verts, faces


def make_box(
    center: Sequence[float],
    size: Sequence[float],
) -> tuple[list[float], list[list[int]]]:
    """Generate a box (6 quad faces).

    Returns flat verts and 0-based face index lists.
    """
    cx, cy, cz = center
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2

    verts = [
        cx - sx,
        cy - sy,
        cz - sz,  # 0: front-bottom-left
        cx + sx,
        cy - sy,
        cz - sz,  # 1: front-bottom-right
        cx + sx,
        cy + sy,
        cz - sz,  # 2: front-top-right
        cx - sx,
        cy + sy,
        cz - sz,  # 3: front-top-left
        cx - sx,
        cy - sy,
        cz + sz,  # 4: back-bottom-left
        cx + sx,
        cy - sy,
        cz + sz,  # 5: back-bottom-right
        cx + sx,
        cy + sy,
        cz + sz,  # 6: back-top-right
        cx - sx,
        cy + sy,
        cz + sz,  # 7: back-top-left
    ]

    faces = [
        [0, 1, 2, 3],  # front  -z
        [5, 4, 7, 6],  # back   +z
        [4, 0, 3, 7],  # left   -x
        [1, 5, 6, 2],  # right  +x
        [3, 2, 6, 7],  # top    +y
        [4, 5, 1, 0],  # bottom -y
    ]

    return verts, faces


# ---------------------------------------------------------------------------
# Build the chick
# ---------------------------------------------------------------------------

# Palette indices.
COL_BLACK = 0
COL_WHITE = 1
COL_LIGHT_YELLOW = 2
COL_YELLOW = 3
COL_DARK_YELLOW = 4
COL_ORANGE = 5
COL_RED = 6
COL_DARK_RED = 7
COL_VERY_LIGHT_YELLOW = 8
COL_MID_DARK_YELLOW = 9
COL_LIGHT_ORANGE = 10
COL_DARK_ORANGE = 11
COL_GRAY = 12
COL_DARK_GRAY = 13
COL_TRANSPARENT = 14
COL_BACKGROUND = 15

# Tile layout on 128x128 texture (each 32x32 pixels = 0.25 UV).
TILE_BODY = (0.0, 0.0, 0.25, 0.25)
TILE_BEAK = (0.25, 0.0, 0.5, 0.25)
TILE_COMB = (0.5, 0.0, 0.75, 0.25)
TILE_EYE = (0.75, 0.0, 1.0, 0.25)
TILE_FEET = (0.0, 0.25, 0.25, 0.5)
TILE_BODY_DARK = (0.25, 0.25, 0.5, 0.5)
TILE_WING = (0.5, 0.25, 0.75, 0.5)


def _build_body(all_verts: list[float], all_faces: list[tuple[list[int], int]]) -> None:
    """Build the main body (egg-shaped sphere)."""
    body_verts, body_rings = make_uv_sphere(
        radius=1.0,
        n_lon=10,
        n_lat=7,
        squash_top=0.9,
        squash_bottom=1.05,
    )
    body_faces_idx = sphere_faces(body_rings, 10)

    base = len(all_verts) // 3
    all_verts.extend(body_verts)
    for face in body_faces_idx:
        shifted = [v + base for v in face]
        all_faces.append((shifted, COL_YELLOW))


def _build_beak(all_verts: list[float], all_faces: list[tuple[list[int], int]]) -> None:
    """Build the beak (small cone at the front)."""
    beak_verts, beak_faces_idx = make_cone(
        base_center=[0.0, 0.05, 0.85],
        tip=[0.0, 0.0, 1.1],
        base_radius=0.18,
        n_segments=5,
    )

    base = len(all_verts) // 3
    all_verts.extend(beak_verts)
    for face in beak_faces_idx:
        shifted = [v + base for v in face]
        all_faces.append((shifted, COL_ORANGE))


def _build_comb(all_verts: list[float], all_faces: list[tuple[list[int], int]]) -> None:
    """Build the comb (single piece on top of the head)."""
    # Single larger comb - a flattened cone shape
    verts, faces_idx = make_cone(
        base_center=[0.0, 0.85, 0.0],
        tip=[0.0, 1.25, 0.0],
        base_radius=0.2,
        n_segments=6,
    )
    base = len(all_verts) // 3
    all_verts.extend(verts)
    for face in faces_idx:
        shifted = [v + base for v in face]
        all_faces.append((shifted, COL_RED))


def _build_eyes(all_verts: list[float], all_faces: list[tuple[list[int], int]]) -> None:
    """Build the eyes (small quads on each side)."""
    eye_y = 0.35  # higher position
    eye_z = 0.7
    eye_size = 0.08

    for side in [-1, 1]:
        cx = side * 0.4  # closer together
        verts, faces_idx = make_box(
            center=[cx, eye_y, eye_z],
            size=[0.05, eye_size, eye_size],
        )
        base = len(all_verts) // 3
        all_verts.extend(verts)
        for face in faces_idx:
            shifted = [v + base for v in face]
            all_faces.append((shifted, COL_BLACK))


def _build_feet(all_verts: list[float], all_faces: list[tuple[list[int], int]]) -> None:
    """Build the feet and legs (connected to body, dark toned)."""
    # Legs - longer for visibility
    leg_length = 0.5
    leg_y_start = -0.95  # bottom of body
    leg_y_end = leg_y_start - leg_length

    for side in [-1, 1]:
        cx = side * 0.25
        # Leg (thin box)
        verts, faces_idx = make_box(
            center=[cx, leg_y_start - leg_length / 2, 0.05],
            size=[0.08, leg_length, 0.08],
        )
        base = len(all_verts) // 3
        all_verts.extend(verts)
        for face in faces_idx:
            shifted = [v + base for v in face]
            all_faces.append((shifted, COL_DARK_GRAY))

        # Foot (at bottom of leg)
        verts, faces_idx = make_box(
            center=[cx, leg_y_end, 0.15],
            size=[0.18, 0.08, 0.22],
        )
        base = len(all_verts) // 3
        all_verts.extend(verts)
        for face in faces_idx:
            shifted = [v + base for v in face]
            all_faces.append((shifted, COL_DARK_GRAY))


def _build_wings(all_verts: list[float], all_faces: list[tuple[list[int], int]]) -> None:
    """Build oval wings on the sides of the body, tilted outward."""
    wing_y = 0.0  # vertical center
    wing_z = 0.0  # centered front-to-back
    tilt_angle = 0.35  # radians (~20 degrees) tilt outward

    for side in [-1, 1]:
        cx = side * 0.88  # closer to body
        # Oval wing shape: squashed sphere
        wing_verts, wing_rings = make_uv_sphere(
            radius=0.45,
            n_lon=8,
            n_lat=5,
            squash_top=0.25,   # very flat
            squash_bottom=0.25,
        )
        wing_faces_idx = sphere_faces(wing_rings, 8)

        # Rotate and offset the wing
        offset_verts = []
        for i in range(0, len(wing_verts), 3):
            x, y, z = wing_verts[i], wing_verts[i + 1], wing_verts[i + 2]
            # Rotate around Z axis (tilt outward - wing tips away from body)
            cos_t = math.cos(tilt_angle * side)
            sin_t = math.sin(tilt_angle * side)
            rx = x * cos_t - y * sin_t
            ry = x * sin_t + y * cos_t
            # Offset to side
            offset_verts.extend([rx + cx, ry + wing_y, z + wing_z])

        base = len(all_verts) // 3
        all_verts.extend(offset_verts)
        for face in wing_faces_idx:
            shifted = [v + base for v in face]
            all_faces.append((shifted, COL_LIGHT_YELLOW))


def build_chick() -> Model:
    """Construct a low-poly baby chick ``Model``.

    Returns
    -------
    Model
        A multi-part chick with body, beak, comb, eyes, feet, and wings.
    """
    all_verts: list[float] = []
    all_faces: list[tuple[list[int], int]] = []

    _build_body(all_verts, all_faces)
    _build_beak(all_verts, all_faces)
    _build_comb(all_verts, all_faces)
    _build_eyes(all_verts, all_faces)
    _build_feet(all_verts, all_faces)
    _build_wings(all_verts, all_faces)

    # Convert to list of lists for ensure_outward.
    all_verts_seq: list[list[float]] = [
        all_verts[i * 3 : i * 3 + 3] for i in range(len(all_verts) // 3)
    ]

    # Build faces with UV projection and winding correction.
    faces: list[Face] = []
    for vids_0based, color in all_faces:
        # Pick tile based on color.
        tile = {
            COL_YELLOW: TILE_BODY,
            COL_DARK_YELLOW: TILE_BODY_DARK,
            COL_LIGHT_YELLOW: TILE_WING,
            COL_ORANGE: TILE_FEET,
            COL_DARK_GRAY: TILE_FEET,
            COL_RED: TILE_COMB,
            COL_BLACK: TILE_EYE,
        }.get(color, TILE_BODY)

        vids_corrected = ensure_outward(vids_0based, all_verts_seq)
        uvs = project_uv(vids_corrected, all_verts_seq, tile, inset=0.15)
        dbl = color == COL_ORANGE  # double-sided for beak/feet
        faces.append(Face(vertex_ids=vids_corrected, uvs=uvs, color=color, dbl=dbl))

    mesh = Mesh(name="chick", vertices=all_verts, faces=faces)

    # Build node hierarchy with separate parts.
    body_node = Node(name="body", mesh=mesh, transform=Transform())

    # Separate meshes for each part for the multi-part structure.
    # We'll split the single mesh into folder children by building separate meshes.

    # Re-build as separate meshes for proper multi-part structure.
    body_v: list[float] = []
    body_f: list[tuple[list[int], int]] = []
    _build_body(body_v, body_f)
    body_verts_seq = [body_v[i * 3 : i * 3 + 3] for i in range(len(body_v) // 3)]
    body_faces: list[Face] = []
    for vids_0based, color in body_f:
        vids_corrected = ensure_outward(vids_0based, body_verts_seq)
        uvs = project_uv(vids_corrected, body_verts_seq, TILE_BODY, inset=0.15)
        body_faces.append(Face(vertex_ids=vids_corrected, uvs=uvs, color=color))
    body_mesh = Mesh(name="body", vertices=body_v, faces=body_faces)
    body_node = Node(name="body", mesh=body_mesh, transform=Transform())

    # Beak
    beak_v: list[float] = []
    beak_f: list[tuple[list[int], int]] = []
    _build_beak(beak_v, beak_f)
    beak_verts_seq = [beak_v[i * 3 : i * 3 + 3] for i in range(len(beak_v) // 3)]
    beak_faces: list[Face] = []
    for vids_0based, color in beak_f:
        vids_corrected = ensure_outward(vids_0based, beak_verts_seq)
        uvs = project_uv(vids_corrected, beak_verts_seq, TILE_BEAK, inset=0.15)
        beak_faces.append(Face(vertex_ids=vids_corrected, uvs=uvs, color=color, dbl=True))
    beak_mesh = Mesh(name="beak", vertices=beak_v, faces=beak_faces)
    beak_node = Node(name="beak", mesh=beak_mesh, transform=Transform())

    # Comb
    comb_v: list[float] = []
    comb_f: list[tuple[list[int], int]] = []
    _build_comb(comb_v, comb_f)
    comb_verts_seq = [comb_v[i * 3 : i * 3 + 3] for i in range(len(comb_v) // 3)]
    comb_faces: list[Face] = []
    for vids_0based, color in comb_f:
        vids_corrected = ensure_outward(vids_0based, comb_verts_seq)
        uvs = project_uv(vids_corrected, comb_verts_seq, TILE_COMB, inset=0.15)
        comb_faces.append(Face(vertex_ids=vids_corrected, uvs=uvs, color=color, dbl=True))
    comb_mesh = Mesh(name="comb", vertices=comb_v, faces=comb_faces)
    comb_node = Node(name="comb", mesh=comb_mesh, transform=Transform())

    # Eyes
    eye_v: list[float] = []
    eye_f: list[tuple[list[int], int]] = []
    _build_eyes(eye_v, eye_f)
    eye_verts_seq = [eye_v[i * 3 : i * 3 + 3] for i in range(len(eye_v) // 3)]
    eye_faces: list[Face] = []
    for vids_0based, color in eye_f:
        vids_corrected = ensure_outward(vids_0based, eye_verts_seq)
        uvs = project_uv(vids_corrected, eye_verts_seq, TILE_EYE, inset=0.15)
        eye_faces.append(Face(vertex_ids=vids_corrected, uvs=uvs, color=color))
    eye_mesh = Mesh(name="eyes", vertices=eye_v, faces=eye_faces)
    eye_node = Node(name="eyes", mesh=eye_mesh, transform=Transform())

    # Feet
    feet_v: list[float] = []
    feet_f: list[tuple[list[int], int]] = []
    _build_feet(feet_v, feet_f)
    feet_verts_seq = [feet_v[i * 3 : i * 3 + 3] for i in range(len(feet_v) // 3)]
    feet_faces: list[Face] = []
    for vids_0based, color in feet_f:
        vids_corrected = ensure_outward(vids_0based, feet_verts_seq)
        uvs = project_uv(vids_corrected, feet_verts_seq, TILE_FEET, inset=0.15)
        feet_faces.append(Face(vertex_ids=vids_corrected, uvs=uvs, color=color, dbl=True, notex=True))
    feet_mesh = Mesh(name="feet", vertices=feet_v, faces=feet_faces)
    feet_node = Node(name="feet", mesh=feet_mesh, transform=Transform())

    # Wings
    wings_v: list[float] = []
    wings_f: list[tuple[list[int], int]] = []
    _build_wings(wings_v, wings_f)
    wings_verts_seq = [wings_v[i * 3 : i * 3 + 3] for i in range(len(wings_v) // 3)]
    wings_faces: list[Face] = []
    for vids_0based, color in wings_f:
        vids_corrected = ensure_outward(vids_0based, wings_verts_seq)
        uvs = project_uv(vids_corrected, wings_verts_seq, TILE_WING, inset=0.15)
        wings_faces.append(Face(vertex_ids=vids_corrected, uvs=uvs, color=color, dbl=True))
    wings_mesh = Mesh(name="wings", vertices=wings_v, faces=wings_faces)
    wings_node = Node(name="wings", mesh=wings_mesh, transform=Transform())

    root = Node(
        name="root",
        children=[body_node, beak_node, comb_node, eye_node, feet_node, wings_node],
    )

    # Build texture.
    texture = Texture(background_color=COL_BACKGROUND)

    # Body tile: yellow with gradient (lighter top, darker bottom).
    texture.paint_tile(TILE_BODY, COL_YELLOW)
    # Paint gradient pixels on body tile.
    tx0, ty0, tx1, ty1 = TILE_BODY
    px0 = int(tx0 * 128)
    py0 = int(ty0 * 128)
    px1 = int(tx1 * 128)
    py1 = int(ty1 * 128)
    for y in range(py0, py1):
        for x in range(px0, px1):
            if (x + y) % 3 == 0:
                texture.set_pixel(x, y, COL_LIGHT_YELLOW)

    # Beak tile: orange.
    texture.paint_tile(TILE_BEAK, COL_ORANGE)
    # Add highlight pixel on beak.
    bx0, by0 = int(TILE_BEAK[0] * 128), int(TILE_BEAK[1] * 128)
    texture.set_pixel(bx0 + 4, by0 + 4, COL_LIGHT_ORANGE)

    # Comb tile: red with darker edge.
    texture.paint_tile(TILE_COMB, COL_RED)
    # Add dark pixels along bottom edge.
    cx0, _cy0, cx1, cy1 = TILE_COMB
    for x in range(int(cx0 * 128), int(cx1 * 128)):
        texture.set_pixel(x, int(cy1 * 128) - 2, COL_DARK_RED)
        texture.set_pixel(x, int(cy1 * 128) - 1, COL_DARK_RED)

    # Eye tile: black.
    texture.paint_tile(TILE_EYE, COL_BLACK)
    # Add white highlight pixel.
    ex0, ey0 = int(TILE_EYE[0] * 128), int(TILE_EYE[1] * 128)
    texture.set_pixel(ex0 + 8, ey0 + 8, COL_WHITE)
    texture.set_pixel(ex0 + 9, ey0 + 8, COL_WHITE)
    texture.set_pixel(ex0 + 8, ey0 + 9, COL_WHITE)
    texture.set_pixel(ex0 + 9, ey0 + 9, COL_WHITE)

    # Feet tile: orange.
    texture.paint_tile(TILE_FEET, COL_ORANGE)

    # Wing tile: lighter yellow with feather-like pattern.
    texture.paint_tile(TILE_WING, COL_LIGHT_YELLOW)
    # Add darker yellow streaks for feather detail.
    wx0, wy0, wx1, wy1 = TILE_WING
    px0 = int(wx0 * 128)
    py0 = int(wy0 * 128)
    px1 = int(wx1 * 128)
    py1 = int(wy1 * 128)
    for y in range(py0, py1):
        for x in range(px0, px1):
            # Diagonal feather pattern
            if (x + y) % 4 == 0:
                texture.set_pixel(x, y, COL_YELLOW)
            elif (x - y) % 6 == 0:
                texture.set_pixel(x, y, COL_VERY_LIGHT_YELLOW)

    # Build custom palette for the chick.
    colors = [
        (0.00, 0.00, 0.00),  # 0  black
        (1.00, 1.00, 1.00),  # 1  white
        (1.00, 0.97, 0.75),  # 2  light yellow
        (1.00, 0.88, 0.45),  # 3  yellow (main body)
        (0.90, 0.72, 0.30),  # 4  dark yellow (shadow)
        (1.00, 0.60, 0.20),  # 5  orange (beak/feet)
        (0.90, 0.22, 0.12),  # 6  red (comb)
        (0.70, 0.15, 0.10),  # 7  dark red (comb shadow)
        (1.00, 0.99, 0.88),  # 8  very light yellow (top highlight)
        (0.85, 0.68, 0.28),  # 9  mid-dark yellow (gradient)
        (1.00, 0.72, 0.35),  # 10 light orange (beak highlight)
        (0.80, 0.50, 0.15),  # 11 dark orange (beak shadow)
        (0.50, 0.50, 0.50),  # 12 gray
        (0.30, 0.30, 0.30),  # 13 dark gray
        (1.00, 1.00, 1.00),  # 14 transparent (reserved)
        (0.92, 0.92, 0.90),  # 15 background (warm gray)
    ]

    # Shading ramps.
    shade_pal_1 = [
        0,  # 0 black -> stays black
        8,  # 1 white -> very light yellow
        8,  # 2 light yellow -> very light yellow
        2,  # 3 yellow -> light yellow (lit)
        3,  # 4 dark yellow -> yellow (lit)
        10,  # 5 orange -> light orange (lit)
        7,  # 6 red -> dark red (lit)
        6,  # 7 dark red -> red (lit)
        2,  # 8 very light yellow -> light yellow
        4,  # 9 mid-dark yellow -> dark yellow
        5,  # 10 light orange -> orange
        5,  # 11 dark orange -> orange
        12,  # 12 gray -> stays
        13,  # 13 dark gray -> stays
        14,  # 14 transparent -> stays
        15,  # 15 background -> stays
    ]
    shade_pal_2 = [
        0,  # 0 black -> stays black
        2,  # 1 white -> light yellow
        3,  # 2 light yellow -> yellow
        4,  # 3 yellow -> dark yellow (shadow)
        9,  # 4 dark yellow -> mid-dark yellow
        5,  # 5 orange -> stays orange
        7,  # 6 red -> dark red (shadow)
        7,  # 7 dark red -> stays
        3,  # 8 very light yellow -> yellow
        9,  # 9 mid-dark yellow -> stays
        5,  # 10 light orange -> orange
        11,  # 11 dark orange -> stays
        13,  # 12 gray -> dark gray
        13,  # 13 dark gray -> stays
        14,  # 14 transparent -> stays
        15,  # 15 background -> stays
    ]

    return Model(
        root=root,
        texture=texture,
        colors=colors,
        shade_pal_1=shade_pal_1,
        shade_pal_2=shade_pal_2,
        transparent_color=COL_TRANSPARENT,
        background_color=COL_BACKGROUND,
        shading_mode=1,
    )


def main() -> None:
    """Entry point: build the chick and write it to ``models/chick.txt``."""
    model = build_chick()
    out_path = Path(__file__).resolve().parent.parent / "models" / "chick.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.write(out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
