"""Generate a low-poly football shoe (soccer cleat) model for picoCAD 2.

Blue + white main tones; a 128x128 texture carries common real-shoe
details: synthetic upper hatch, a side swoosh accent stripe, a laced
tongue, a firm-ground tread plate, stud caps and a heel counter.

Mesh is built by lofting 6-point cross-section arcs along 7 stations
from heel to toe, plus a separate sole band and 6 pyramid studs. The
whole model is centered at the origin so the outward-winding heuristic
is reliable. Output is ASCII-only JSON.

Run::

    uv run python scripts/football_shoe/gen_football_shoe_glm-5.2.py

Outputs ``models/football_shoe/football_shoe_glm-5.2.txt``.
"""

from __future__ import annotations

import math
from pathlib import Path

from picocad.model import Camera, ExportSettings, Face, Mesh, Model, Node
from picocad.texture import Texture
from picocad.uv import ensure_outward, project_uv

# ----------------------------------------------------------------------------
# Palette -- a cool blue/white ramp with a couple of grays for the sole and a
# dedicated warm-tan background slot (15) so the cool shoe contrasts strongly
# against the viewport background. Slot 14 stays reserved for transparency.
# ----------------------------------------------------------------------------
COLORS: list[tuple[float, float, float]] = [
    (0.05, 0.06, 0.10),  # 0  near-black (outline / deepest shadow)
    (1.00, 1.00, 1.00),  # 1  pure white
    (0.62, 0.80, 0.95),  # 2  light blue
    (0.30, 0.52, 0.85),  # 3  main blue  (upper base)
    (0.12, 0.28, 0.62),  # 4  dark blue  (sole / heel base)
    (0.05, 0.13, 0.38),  # 5  navy
    (0.80, 0.90, 0.98),  # 6  pale blue  (tongue base)
    (0.45, 0.80, 0.95),  # 7  cyan accent (stitches / swoosh trim)
    (0.90, 0.92, 0.95),  # 8  off-white
    (0.30, 0.33, 0.38),  # 9  dark gray (tread grips)
    (0.55, 0.58, 0.63),  # 10 mid gray
    (0.78, 0.80, 0.85),  # 11 light gray
    (0.10, 0.22, 0.52),  # 12 shadow blue (seam lines)
    (0.86, 0.88, 0.92),  # 13 stud pale
    (1.00, 1.00, 1.00),  # 14 reserved transparent
    (0.42, 0.34, 0.26),  # 15 warm tan background (contrasts cool shoe)
]

# Lit / shadow remap ramps. Lighter sibling on the lit row, darker on shadow.
SHADE_PAL_1 = [0, 9, 6, 2, 3, 4, 1, 6, 1, 10, 11, 8, 4, 1, 31, 31]
SHADE_PAL_2 = [0, 11, 3, 4, 5, 0, 2, 2, 10, 0, 9, 10, 5, 8, 31, 31]

TRANSPARENT_COLOR = 14
BACKGROUND_COLOR = 15

# ----------------------------------------------------------------------------
# Texture tiles (8x8 grid, each tile 16x16 px = 0.125 in UV space).
#   A blue upper   (0.000,0.000,0.125,0.125)
#   B side swoosh  (0.125,0.000,0.250,0.125)
#   C tongue/laces (0.250,0.000,0.375,0.125)
#   D sole tread   (0.000,0.125,0.125,0.250)
#   E stud cap     (0.125,0.125,0.250,0.250)
#   F heel counter (0.250,0.125,0.375,0.250)
#   G toe cap      (0.000,0.250,0.125,0.375)
# ----------------------------------------------------------------------------
T_A = (0.000, 0.000, 0.125, 0.125)
T_B = (0.125, 0.000, 0.250, 0.125)
T_C = (0.250, 0.000, 0.375, 0.125)
T_D = (0.000, 0.125, 0.125, 0.250)
T_E = (0.125, 0.125, 0.250, 0.250)
T_F = (0.250, 0.125, 0.375, 0.250)
T_G = (0.000, 0.250, 0.125, 0.375)

PX = 16  # pixels per tile side


def _paint_tile_rect(tex: Texture, x0: int, y0: int, color: int) -> None:
    for y in range(PX):
        for x in range(PX):
            tex.set_pixel(x0 + x, y0 + y, color)


def _ring(tex: Texture, x0: int, y0: int, color: int) -> None:
    for i in range(PX):
        tex.set_pixel(x0 + i, y0, color)
        tex.set_pixel(x0 + i, y0 + PX - 1, color)
        tex.set_pixel(x0, y0 + i, color)
        tex.set_pixel(x0 + PX - 1, y0 + i, color)


def build_texture() -> Texture:
    tex = Texture(background_color=TRANSPARENT_COLOR)

    # --- Tile A : blue synthetic upper with diagonal hatch + seam ring ---
    ax, ay = 0, 0
    _paint_tile_rect(tex, ax, ay, 3)
    for y in range(PX):
        for x in range(PX):
            if (x + y) % 3 == 0:
                tex.set_pixel(ax + x, ay + y, 2)  # light-blue hatch
    _ring(tex, ax, ay, 12)
    tex.set_pixel(ax + 4, ay + 4, 6)
    tex.set_pixel(ax + 11, ay + 11, 6)
    tex.set_pixel(ax + 11, ay + 4, 6)

    # --- Tile B : white side panel with a swoosh-style accent stripe ---
    bx, by = PX, 0
    _paint_tile_rect(tex, bx, by, 1)
    for x in range(PX):
        yc = round(5 + 3.2 * math.sin(x * 0.45))
        for dy in (-1, 0, 1):
            yy = by + yc + dy
            if 0 <= yy - by < PX:
                tex.set_pixel(bx + x, yy, 3 if dy == 0 else 7)
    _ring(tex, bx, by, 0)

    # --- Tile C : tongue with vertical lace cords + eyelets ---
    cx, cy = PX * 2, 0
    _paint_tile_rect(tex, cx, cy, 6)
    for col in (3, 6, 9, 12):
        for y in range(PX):
            tex.set_pixel(cx + col, cy + y, 1)  # lace cord
    # crossing diagonals between cords
    for y in range(2, PX - 2, 3):
        tex.set_pixel(cx + 3, cy + y, 3)
        tex.set_pixel(cx + 6, cy + y + 1, 3)
        tex.set_pixel(cx + 9, cy + y, 3)
        tex.set_pixel(cx + 12, cy + y + 1, 3)
    # eyelets
    for col in (3, 6, 9, 12):
        tex.set_pixel(cx + col, cy + 1, 0)
        tex.set_pixel(cx + col, cy + PX - 2, 0)
    _ring(tex, cx, cy, 12)

    # --- Tile D : dark-blue sole plate with white tread grip bars ---
    dx, dy = 0, PX
    _paint_tile_rect(tex, dx, dy, 4)
    for row in (3, 7, 11):
        for x in range(PX):
            tex.set_pixel(dx + x, dy + row, 1 if x % 4 != 0 else 9)
            tex.set_pixel(dx + x, dy + row + 1, 1 if x % 4 != 0 else 9)
    _ring(tex, dx, dy, 5)

    # --- Tile E : white stud cap with cyan accent ring + blue hub ---
    ex, ey = PX, PX
    _paint_tile_rect(tex, ex, ey, 1)
    cxp, cyp = ex + PX // 2, ey + PX // 2
    for y in range(PX):
        for x in range(PX):
            d = math.hypot(x - PX / 2, y - PX / 2)
            if 3.2 < d < 4.6:
                tex.set_pixel(ex + x, ey + y, 7)
            elif d <= 2.0:
                tex.set_pixel(ex + x, ey + y, 3)
    _ = cxp, cyp

    # --- Tile F : heel counter with a logo-style patch ---
    fx, fy = PX * 2, PX
    _paint_tile_rect(tex, fx, fy, 4)
    for y in range(5, 11):
        for x in range(4, 12):
            tex.set_pixel(fx + x, fy + y, 1)  # white patch
    # little diagonal mark inside the patch
    for k in range(4):
        tex.set_pixel(fx + 5 + k, fy + 6 + k, 3)
        tex.set_pixel(fx + 5 + k, fy + 9 - k, 3)
    _ring(tex, fx, fy, 12)
    for i in range(PX):
        tex.set_pixel(fx + i, fy + 1, 7)
        tex.set_pixel(fx + 1, fy + i, 7)

    # --- Tile G : toe cap with reinforced diagonal stitches ---
    gx, gy = 0, PX * 2
    _paint_tile_rect(tex, gx, gy, 3)
    for k in range(2, 14, 3):
        tex.set_pixel(gx + k, gy + (14 - k), 7)
        tex.set_pixel(gx + k, gy + (14 - k) + 1, 7)
        tex.set_pixel(gx + k, gy + (k) % PX, 2)
    _ring(tex, gx, gy, 4)
    tex.set_pixel(gx + 8, gy + 8, 4)
    tex.set_pixel(gx + 9, gy + 9, 4)

    return tex


# ----------------------------------------------------------------------------
# Geometry
# ----------------------------------------------------------------------------
SOLE_Y = -0.30  # the upper's bottom line; the sole sits just under it

# 7 stations from heel to toe: (x, half-width, top height above sole)
STATIONS: list[tuple[float, float, float]] = [
    (-1.00, 0.200, 0.42),  # 0 heel
    (-0.70, 0.255, 0.50),  # 1
    (-0.30, 0.275, 0.55),  # 2 arch (tallest)
    (+0.05, 0.270, 0.52),  # 3 ball
    (+0.45, 0.255, 0.40),  # 4 forefoot
    (+0.78, 0.205, 0.27),  # 5
    (+0.98, 0.135, 0.16),  # 6 toe start
]

ARC_POINTS = 6  # cross-section arc samples per station


def station_arc(x: float, w: float, h: float) -> list[tuple[float, float, float]]:
    """Return 6 arc points (open at the bottom) for one cross-section.

    Index order: 0 outer-bottom, 1 outer-upper, 2 outer-top,
                 3 inner-top, 4 inner-upper, 5 inner-bottom.
    The span 2<->3 is the flat-ish tongue region across the top.
    """
    y0 = SOLE_Y
    return [
        (x, y0, +w),  # 0 outer bottom
        (x, y0 + 0.70 * h, +w),  # 1 outer upper
        (x, y0 + h, +0.45 * w),  # 2 outer top
        (x, y0 + h, -0.45 * w),  # 3 inner top
        (x, y0 + 0.70 * h, -w),  # 4 inner upper
        (x, y0, -w),  # 5 inner bottom
    ]


def upper_tile(i: int, k: int) -> tuple[float, float, float, float]:
    """Pick a texture tile for the loft quad between station i and i+1, strip k."""
    # near the toe everything reads as the toe cap
    if i >= 5:
        return T_G
    # midfoot top span (k == 2) carries the laced tongue
    if k == 2:
        return T_C if i in (2, 3) else T_A
    # outer side (k 0/1) mid-body carries the swoosh panel
    if k in (0, 1) and 1 <= i <= 3:
        return T_B
    # heel back (station 0) upper strips get the heel-counter tile
    if i == 0 and k in (1, 2, 3):
        return T_F
    return T_A


def make_face(
    vids: list[int],
    verts: list[float],
    tile: tuple[float, float, float, float],
    color: int,
    *,
    inset: float = 0.10,
) -> Face:
    """Ensure outward winding, then planar-project UVs into ``tile``.

    ``verts`` is the mesh's flat ``[x,y,z, ...]`` array; both UV helpers
    index it as ``all_verts[i] -> (x,y,z)``, so group it here.
    """
    grouped = [(verts[i], verts[i + 1], verts[i + 2]) for i in range(0, len(verts), 3)]
    vids = ensure_outward(vids, grouped)
    uvs = project_uv(vids, grouped, tile, inset=inset)
    return Face(vertex_ids=vids, uvs=uvs, color=color)


def build_upper() -> Mesh:
    verts: list[float] = []
    for x, w, h in STATIONS:
        for px, py, pz in station_arc(x, w, h):
            verts.extend([px, py, pz])

    # toe tip apex
    verts.extend([1.08, SOLE_Y + 0.06, 0.0])
    toe_tip = len(verts) // 3 - 1
    # heel cup center
    verts.extend([-1.04, SOLE_Y + 0.20, 0.0])
    heel_c = len(verts) // 3 - 1

    faces: list[Face] = []

    # loft quads between successive stations
    for i in range(len(STATIONS) - 1):
        for k in range(ARC_POINTS - 1):
            a = i * ARC_POINTS + k
            b = i * ARC_POINTS + (k + 1)
            c = (i + 1) * ARC_POINTS + (k + 1)
            d = (i + 1) * ARC_POINTS + k
            tile = upper_tile(i, k)
            color = 3 if tile in (T_A, T_C, T_G) else (1 if tile == T_B else 4)
            faces.append(make_face([a, b, c, d], verts, tile, color))

    # toe fan: close station 6's arc into the toe-tip apex
    s6 = (len(STATIONS) - 1) * ARC_POINTS
    for k in range(ARC_POINTS):
        a = s6 + k
        b = s6 + (k + 1) % ARC_POINTS
        faces.append(make_face([a, b, toe_tip], verts, T_G, 3))

    # heel fan: close station 0's arc into the heel-cup vertex
    for k in range(ARC_POINTS):
        a = k
        b = (k + 1) % ARC_POINTS
        faces.append(make_face([a, b, heel_c], verts, T_F, 4))

    return Mesh(name="upper", vertices=verts, faces=faces)


def build_sole() -> Mesh:
    # 8-point footprint outline (top-view, clockwise): toe-front, outer side,
    # heel-back, inner side.
    outline: list[tuple[float, float]] = [
        (1.06, 0.00),  # 0 toe front
        (0.50, 0.26),  # 1 forefoot outer
        (-0.10, 0.28),  # 2 mid outer
        (-0.80, 0.22),  # 3 heel outer
        (-1.04, 0.00),  # 4 heel back
        (-0.80, -0.22),  # 5 heel inner
        (-0.10, -0.28),  # 6 mid inner
        (0.50, -0.26),  # 7 forefoot inner
    ]
    y_top = SOLE_Y - 0.02
    y_bot = SOLE_Y - 0.10

    verts: list[float] = []
    for x, z in outline:  # top rim
        verts.extend([x, y_top, z])
    for x, z in outline:  # bottom rim
        verts.extend([x, y_bot, z])
    verts.extend([0.0, y_bot, 0.0])  # bottom fan center
    center = len(verts) // 3 - 1

    faces: list[Face] = []
    n = len(outline)

    # outer rim band (top -> bottom)
    for k in range(n):
        a = k
        b = (k + 1) % n
        c = n + (k + 1) % n
        d = n + k
        faces.append(make_face([a, b, c, d], verts, T_D, 4))

    # bottom cap as a fan of triangles (keep max face arity <= 8)
    for k in range(n):
        a = n + k
        b = n + (k + 1) % n
        faces.append(make_face([a, b, center], verts, T_D, 4))

    return Mesh(name="sole", vertices=verts, faces=faces)


def build_studs() -> Mesh:
    # 6 firm-ground studs as downward pyramids: apex below, base buried in sole.
    positions = [
        (0.50, 0.16),
        (0.50, -0.16),  # forefoot
        (-0.15, 0.18),
        (-0.15, -0.18),  # mid
        (-0.82, 0.13),
        (-0.82, -0.13),  # heel
    ]
    r = 0.06
    y_base = SOLE_Y - 0.10  # sits at the sole bottom
    y_apex = SOLE_Y - 0.22  # pokes below

    verts: list[float] = []
    faces: list[Face] = []

    for sx, sz in positions:
        base0 = len(verts) // 3
        # square base corners
        for dx, dz in ((-r, -r), (+r, -r), (+r, +r), (-r, +r)):
            verts.extend([sx + dx, y_base, sz + dz])
        # apex
        verts.extend([sx, y_apex, sz])
        apex = len(verts) // 3 - 1

        for k in range(4):
            a = base0 + k
            b = base0 + (k + 1) % 4
            faces.append(make_face([a, b, apex], verts, T_E, 1))

    return Mesh(name="studs", vertices=verts, faces=faces)


def build_football_shoe() -> Model:
    upper = build_upper()
    sole = build_sole()
    studs = build_studs()

    root = Node(
        name="root",
        children=[
            Node(name="upper", mesh=upper),
            Node(name="sole", mesh=sole),
            Node(name="studs", mesh=studs),
        ],
    )

    tex = build_texture()

    return Model(
        root=root,
        texture=tex,
        colors=list(COLORS),
        shade_pal_1=list(SHADE_PAL_1),
        shade_pal_2=list(SHADE_PAL_2),
        transparent_color=TRANSPARENT_COLOR,
        background_color=BACKGROUND_COLOR,
        motion_duration=2,
        shading_mode=1,
        camera=Camera(
            pos=(3.0, 1.7, 3.2),
            target=(0.0, 0.0, 0.0),
            distance_to_target=4.6,
            omega=-1.0,
            theta=0.38,
        ),
        export_settings=ExportSettings(
            watermark="#picoCAD2",
            anim="spin",
            speed=5,
            outline_size=1,
            outline_color=0,
        ),
    )


def main() -> None:
    model = build_football_shoe()
    script_name = Path(__file__).resolve().name
    model_name = script_name.removeprefix("gen_").replace(".py", ".txt")
    out = Path(__file__).resolve().parent.parent.parent / "models" / "football_shoe" / model_name
    out.parent.mkdir(parents=True, exist_ok=True)
    model.write(out)

    n_verts = sum(len(m.vertices) // 3 for m in (build_upper(), build_sole(), build_studs()))
    n_faces = sum(len(m.faces) for m in (build_upper(), build_sole(), build_studs()))
    print(f"wrote {out}")
    print(f"  vertices: {n_verts}")
    print(f"  faces:    {n_faces}")
    print(f"  palette:  16 colors, background slot {BACKGROUND_COLOR} (warm tan)")
    print("  tiles:    A upper / B swoosh / C tongue / D tread / E stud / F heel / G toecap")


if __name__ == "__main__":
    main()
