#!/usr/bin/env python3
"""Generate a low-poly football shoe (soccer cleat) for picoCAD 2.

Blue and white colour scheme with textured details: side swoosh, toe cap
stitching, stud pattern, heel counter, tongue logo, lace holes.
"""

from __future__ import annotations

from pathlib import Path

from picocad.model import (
    Camera,
    ExportSettings,
    Face,
    Mesh,
    Model,
    Node,
    SpritesheetSettings,
)
from picocad.texture import Texture
from picocad.uv import project_uv

COLORS: list[tuple[float, float, float]] = [
    (0.04, 0.04, 0.06),
    (0.95, 0.95, 0.97),
    (0.14, 0.30, 0.76),
    (0.09, 0.18, 0.52),
    (0.28, 0.48, 0.92),
    (0.05, 0.10, 0.30),
    (0.76, 0.76, 0.80),
    (0.52, 0.52, 0.56),
    (0.28, 0.28, 0.32),
    (0.84, 0.84, 0.87),
    (0.20, 0.40, 0.85),
    (0.62, 0.62, 0.66),
    (0.07, 0.07, 0.10),
    (0.92, 0.93, 0.96),
    (1.00, 1.00, 1.00),
    (0.11, 0.24, 0.62),
]

SHADE_1: list[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
SHADE_2: list[int] = [0, 9, 3, 5, 2, 5, 7, 8, 12, 6, 3, 7, 0, 9, 14, 5]

T_OUTER = (0.0, 0.0, 0.125, 0.125)
T_INNER = (0.125, 0.0, 0.25, 0.125)
T_TOE = (0.25, 0.0, 0.375, 0.125)
T_STUD = (0.375, 0.0, 0.5, 0.125)
T_HEEL = (0.5, 0.0, 0.625, 0.125)
T_TONGUE = (0.625, 0.0, 0.75, 0.125)
T_VAMP = (0.75, 0.0, 0.875, 0.125)
T_SOLE = (0.0, 0.125, 0.125, 0.25)


def _verts() -> list[float]:
    v: list[float] = []

    def pt(x: float, y: float, z: float) -> None:
        v.extend([x, y, z])

    pt(1.50, 0.08, 0.00)
    pt(1.10, 0.02, 0.35)
    pt(1.10, 0.02, -0.35)
    pt(0.50, 0.00, 0.43)
    pt(0.50, 0.00, -0.43)
    pt(-0.20, 0.00, 0.38)
    pt(-0.20, 0.00, -0.38)
    pt(-0.90, 0.00, 0.30)
    pt(-0.90, 0.00, -0.30)
    pt(-1.30, 0.02, 0.18)
    pt(-1.30, 0.02, -0.18)
    pt(1.18, 0.42, 0.22)
    pt(1.18, 0.42, -0.22)
    pt(0.50, 0.68, 0.36)
    pt(0.50, 0.68, -0.36)
    pt(-0.20, 0.85, 0.32)
    pt(-0.20, 0.85, -0.32)
    pt(-0.90, 0.95, 0.25)
    pt(-0.90, 0.95, -0.25)
    pt(-1.30, 0.72, 0.12)
    pt(-1.30, 0.72, -0.12)
    pt(0.10, 1.02, 0.15)
    pt(0.10, 1.02, -0.15)
    pt(-0.50, 1.08, 0.10)
    pt(-0.50, 1.08, -0.10)
    pt(0.88, 0.00, 0.30)
    pt(0.88, 0.00, 0.18)
    pt(0.75, 0.00, 0.18)
    pt(0.75, 0.00, 0.30)
    pt(0.88, -0.13, 0.30)
    pt(0.88, -0.13, 0.18)
    pt(0.75, -0.13, 0.18)
    pt(0.75, -0.13, 0.30)
    pt(0.88, 0.00, -0.30)
    pt(0.88, 0.00, -0.18)
    pt(0.75, 0.00, -0.18)
    pt(0.75, 0.00, -0.30)
    pt(0.88, -0.13, -0.30)
    pt(0.88, -0.13, -0.18)
    pt(0.75, -0.13, -0.18)
    pt(0.75, -0.13, -0.30)
    pt(-0.80, 0.00, 0.24)
    pt(-0.80, 0.00, 0.12)
    pt(-0.95, 0.00, 0.12)
    pt(-0.95, 0.00, 0.24)
    pt(-0.80, -0.13, 0.24)
    pt(-0.80, -0.13, 0.12)
    pt(-0.95, -0.13, 0.12)
    pt(-0.95, -0.13, 0.24)
    pt(-0.80, 0.00, -0.24)
    pt(-0.80, 0.00, -0.12)
    pt(-0.95, 0.00, -0.12)
    pt(-0.95, 0.00, -0.24)
    pt(-0.80, -0.13, -0.24)
    pt(-0.80, -0.13, -0.12)
    pt(-0.95, -0.13, -0.12)
    pt(-0.95, -0.13, -0.24)
    return v


def _paint_texture() -> Texture:
    tex = Texture(background_color=5)

    tex.paint_tile(T_OUTER, 2)
    for y in range(16):
        for x in range(16):
            if abs(x - y - 2) < 3:
                tex.set_pixel(x, y, 1)
            elif abs(x - y - 5) < 1:
                tex.set_pixel(x, y, 3)
    for y in range(16):
        for x in range(16):
            if (x + y) % 7 == 0:
                tex.set_pixel(x, y, 15)

    tex.paint_tile(T_INNER, 2)
    for y in range(16):
        for x in range(16):
            px = x + 16
            if abs((15 - x) - y - 2) < 3:
                tex.set_pixel(px, y, 1)
            elif abs((15 - x) - y - 5) < 1:
                tex.set_pixel(px, y, 3)
    for y in range(16):
        for x in range(16):
            px = x + 16
            if (x + y) % 7 == 0:
                tex.set_pixel(px, y, 15)

    tex.paint_tile(T_TOE, 9)
    for x in range(32, 48):
        tex.set_pixel(x, 1, 11)
        tex.set_pixel(x, 14, 11)
    for y in range(1, 15):
        tex.set_pixel(33, y, 11)
        tex.set_pixel(46, y, 11)
    for x in range(35, 45):
        tex.set_pixel(x, 4, 13)
        tex.set_pixel(x, 5, 1)

    tex.paint_tile(T_STUD, 8)
    for y in range(5, 11):
        for x in range(53, 59):
            tex.set_pixel(x, y, 7)
    for x in range(48, 64):
        tex.set_pixel(x, 0, 12)
        tex.set_pixel(x, 15, 12)

    tex.paint_tile(T_HEEL, 2)
    for y in range(4, 12):
        for x in range(68, 76):
            tex.set_pixel(x, y, 1)
    for x in range(67, 77):
        tex.set_pixel(x, 3, 3)
        tex.set_pixel(x, 12, 3)
    for y in range(3, 13):
        tex.set_pixel(67, y, 3)
        tex.set_pixel(76, y, 3)
    for y in range(13, 16):
        for x in range(64, 80):
            tex.set_pixel(x, y, 4)

    tex.paint_tile(T_TONGUE, 2)
    for y in range(5, 11):
        for x in range(85, 91):
            tex.set_pixel(x, y, 1)
    for x in range(84, 92):
        tex.set_pixel(x, 3, 4)
        tex.set_pixel(x, 4, 4)
    for y in range(12, 16):
        for x in range(80, 96):
            tex.set_pixel(x, y, 3)

    tex.paint_tile(T_VAMP, 2)
    for i in range(4):
        cx = 99 + i * 3
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0:
                    tex.set_pixel(cx + dx, 5 + dy, 0)
                    tex.set_pixel(cx + dx, 10 + dy, 0)
                elif abs(dx) + abs(dy) == 1:
                    tex.set_pixel(cx + dx, 5 + dy, 1)
                    tex.set_pixel(cx + dx, 10 + dy, 1)
    for y in range(13, 16):
        for x in range(96, 112):
            tex.set_pixel(x, y, 3)

    tex.paint_tile(T_SOLE, 6)
    for cx, cy in [(4, 20), (10, 20), (4, 27), (10, 27)]:
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                tex.set_pixel(cx + dx, cy + dy, 8)
    for y in range(16, 32):
        for x in range(0, 16):
            if (x + y) % 5 == 0:
                tex.set_pixel(x, y, 7)
    for x in range(0, 16):
        tex.set_pixel(x, 16, 11)
        tex.set_pixel(x, 31, 11)

    return tex


def build_football_shoe() -> Model:
    v = _verts()
    vv = [(v[i], v[i + 1], v[i + 2]) for i in range(0, len(v), 3)]

    faces: list[Face] = []

    def add(
        vids: list[int],
        tile: tuple[float, float, float, float],
        color: int,
        dbl: bool | None = None,
    ) -> None:
        uvs = project_uv(vids, vv, tile)
        faces.append(Face(vertex_ids=vids, uvs=uvs, color=color, dbl=dbl))

    add([1, 11, 13, 3], T_OUTER, 2)
    add([3, 13, 15, 5], T_OUTER, 2)
    add([5, 15, 17, 7], T_OUTER, 2)
    add([7, 17, 19, 9], T_HEEL, 2)

    add([2, 4, 14, 12], T_INNER, 2)
    add([4, 6, 16, 14], T_INNER, 2)
    add([6, 8, 18, 16], T_INNER, 2)
    add([8, 10, 20, 18], T_HEEL, 2)

    add([0, 1, 2], T_SOLE, 6)
    add([1, 3, 4, 2], T_SOLE, 6)
    add([3, 5, 6, 4], T_SOLE, 6)
    add([5, 7, 8, 6], T_SOLE, 6)
    add([7, 9, 10, 8], T_SOLE, 6)

    add([0, 11, 1], T_TOE, 9)
    add([0, 12, 11], T_TOE, 9)
    add([0, 2, 12], T_TOE, 9)

    add([12, 14, 13, 11], T_VAMP, 2)

    add([9, 19, 20, 10], T_HEEL, 2)

    add([21, 22, 24, 23], T_TONGUE, 2, dbl=True)

    add([25, 28, 32, 29], T_STUD, 8)
    add([26, 30, 31, 27], T_STUD, 8)
    add([25, 29, 30, 26], T_STUD, 8)
    add([28, 27, 31, 32], T_STUD, 8)
    add([29, 32, 31, 30], T_STUD, 8)

    add([33, 37, 40, 36], T_STUD, 8)
    add([34, 35, 39, 38], T_STUD, 8)
    add([33, 34, 38, 37], T_STUD, 8)
    add([36, 40, 39, 35], T_STUD, 8)
    add([37, 38, 39, 40], T_STUD, 8)

    add([41, 44, 48, 45], T_STUD, 8)
    add([42, 46, 47, 43], T_STUD, 8)
    add([41, 45, 46, 42], T_STUD, 8)
    add([44, 43, 47, 48], T_STUD, 8)
    add([45, 48, 47, 46], T_STUD, 8)

    add([49, 53, 56, 52], T_STUD, 8)
    add([50, 51, 55, 54], T_STUD, 8)
    add([49, 50, 54, 53], T_STUD, 8)
    add([52, 56, 55, 51], T_STUD, 8)
    add([53, 54, 55, 56], T_STUD, 8)

    mesh = Mesh(name="football_shoe", vertices=v, faces=faces)
    shoe = Node(name="shoe", mesh=mesh)
    root = Node(name="root", children=[shoe])

    tex = _paint_texture()

    return Model(
        root=root,
        texture=tex,
        colors=COLORS,
        shade_pal_1=SHADE_1,
        shade_pal_2=SHADE_2,
        background_color=5,
        transparent_color=14,
        camera=Camera(
            pos=(2.5, 2.0, 2.5),
            target=(0.1, 0.4, 0.0),
            distance_to_target=3.82,
            omega=0.765,
            theta=0.432,
        ),
        export_settings=ExportSettings(
            anim="spin",
            speed=5,
            size=128,
            scale=3,
            watermark="#picoCAD2",
        ),
        spritesheet_settings=SpritesheetSettings(
            frame_width=48,
            num_frames=8,
            cam_dist=4.0,
            cam_target_y=0.3,
            cam_theta=0.3,
            cam_ortho=True,
        ),
        shading_mode=1,
        face_mode=2,
        motion_duration=2,
    )


def main() -> None:
    model = build_football_shoe()
    out = Path("models/football_shoe/football_shoe_qwen-3.7-plus.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    model.write(out)
    print(f"Wrote {out}")
    shoe_mesh = model.root.children[0].mesh
    assert shoe_mesh is not None
    nv = len(shoe_mesh.vertices) // 3
    nf = len(shoe_mesh.faces)
    print(f"  {nv} vertices, {nf} faces")


if __name__ == "__main__":
    main()
