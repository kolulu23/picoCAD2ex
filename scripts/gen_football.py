"""Recipe: low-poly football (truncated icosahedron) for picoCAD 2.

Generates the classic soccer-ball pattern -- 12 black pentagons + 20 white
hexagons, derived by truncating every edge of an icosahedron at 1/3 and 2/3
of its length. Each face is planar-UV-mapped onto a tile of the 128x128
texture, with pentagon tiles painted black and hexagon tiles left white.

This file is the **football-specific** layer. Replace it with another
recipe to build a different model -- the ``picocad`` package underneath
is reusable and knows nothing about icosahedra.

Run::

    uv run python scripts/gen_football.py

Outputs ``models/football.txt``.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING

from picocad.model import Camera, Face, Mesh, Model, Node
from picocad.texture import Texture
from picocad.uv import basis, ensure_outward, project_uv

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

# ----------------------------------------------------------------------- types
Vec3 = tuple[float, float, float]

# Icosahedron + truncation constants ------------------------------------------------
PHI: float = (1.0 + math.sqrt(5.0)) / 2.0


def _normalize(v: Iterable[float]) -> list[float]:
    """Project ``v`` onto the unit sphere (returns a list of 3 floats)."""
    coords = list(v)
    length = math.sqrt(sum(c * c for c in coords))
    if length == 0.0:
        return [0.0, 0.0, 0.0]
    return [c / length for c in coords]


# ---------------------------------------------------------------- icosahedron
_ico_verts: list[list[float]] = [
    _normalize(v)
    for v in [
        (-1, PHI, 0),
        (1, PHI, 0),
        (-1, -PHI, 0),
        (1, -PHI, 0),
        (0, -1, PHI),
        (0, 1, PHI),
        (0, -1, -PHI),
        (0, 1, -PHI),
        (PHI, 0, -1),
        (PHI, 0, 1),
        (-PHI, 0, -1),
        (-PHI, 0, 1),
    ]
]


def _edge_length(verts: Sequence[Sequence[float]]) -> float:
    """Smallest pairwise distance among ``verts`` -- the icosahedron edge length."""
    return min(
        math.dist(verts[i], verts[j])
        for i in range(len(verts))
        for j in range(i + 1, len(verts))
    )


_EDGE: float = _edge_length(_ico_verts)


def _ico_faces() -> list[list[int]]:
    """All 20 equilateral triangular faces of the icosahedron as vertex-id triples."""
    out: list[list[int]] = []
    for i in range(12):
        for j in range(i + 1, 12):
            if abs(math.dist(_ico_verts[i], _ico_verts[j]) - _EDGE) > 1e-6:
                continue
            for k in range(j + 1, 12):
                if (
                    abs(math.dist(_ico_verts[i], _ico_verts[k]) - _EDGE) <= 1e-6
                    and abs(math.dist(_ico_verts[j], _ico_verts[k]) - _EDGE) <= 1e-6
                ):
                    out.append([i, j, k])
    assert len(out) == 20, f"icosahedron must have 20 faces, got {len(out)}"
    return out


def _edges() -> list[tuple[int, int]]:
    """All 30 undirected edges ``(min_id, max_id)`` of the icosahedron."""
    seen: set[tuple[int, int]] = set()
    for a, b, c in _ico_faces():
        seen.add((min(a, b), max(a, b)))
        seen.add((min(b, c), max(b, c)))
        seen.add((min(a, c), max(a, c)))
    assert len(seen) == 30
    return sorted(seen)


# ----------------------------------------------------------------- truncation
def _truncate_edges() -> tuple[list[Vec3], dict[tuple[int, int], tuple[int, int]]]:
    """Truncate every icosahedron edge into two new vertices (1/3 and 2/3 along).

    Returns
    -------
    verts
        The 60 new vertices (2 per edge x 30 edges).
    edge_cut
        Map ``(min_id, max_id) -> (idx_near_min, idx_near_max)`` for later
        topology construction.
    """
    verts: list[Vec3] = []
    edge_cut: dict[tuple[int, int], tuple[int, int]] = {}
    for a, b in _edges():
        va, vb = _ico_verts[a], _ico_verts[b]
        p_a: Vec3 = (
            va[0] + (vb[0] - va[0]) / 3,
            va[1] + (vb[1] - va[1]) / 3,
            va[2] + (vb[2] - va[2]) / 3,
        )
        p_b: Vec3 = (
            va[0] + 2 * (vb[0] - va[0]) / 3,
            va[1] + 2 * (vb[1] - va[1]) / 3,
            va[2] + 2 * (vb[2] - va[2]) / 3,
        )
        edge_cut[(a, b)] = (len(verts), len(verts) + 1)
        verts.append(p_a)
        verts.append(p_b)
    assert len(verts) == 60
    return verts, edge_cut


def _edge_cut(
    u: int, v: int, edge_cut: dict[tuple[int, int], tuple[int, int]]
) -> tuple[int, int]:
    """Return ``(idx_near_u, idx_near_v)`` for edge ``(u, v)`` (0-based)."""
    pair = edge_cut[(min(u, v), max(u, v))]
    return pair if u < v else (pair[1], pair[0])


# ----------------------------------------------------------------- face lists
def _hexagons(edge_cut: dict[tuple[int, int], tuple[int, int]]) -> list[list[int]]:
    """20 hexagonal faces -- one per icosahedron triangle, walking its 3 edges."""
    out: list[list[int]] = []
    for a, b, c in _ico_faces():
        ab0, ab1 = _edge_cut(a, b, edge_cut)
        bc0, bc1 = _edge_cut(b, c, edge_cut)
        ca0, ca1 = _edge_cut(c, a, edge_cut)
        out.append([ab0, ab1, bc0, bc1, ca0, ca1])
    return out


def _pentagons(
    edge_cut: dict[tuple[int, int], tuple[int, int]],
    all_verts: Sequence[Vec3],
) -> list[list[int]]:
    """12 pentagonal faces -- one per icosahedron vertex, CCW around its outward normal."""
    neighbours: dict[int, list[int]] = {i: [] for i in range(12)}
    for a, b in _edges():
        neighbours[a].append(b)
        neighbours[b].append(a)

    out: list[list[int]] = []
    for v in range(12):
        t1, t2 = basis(all_verts[v])
        # Sort neighbouring vertices CCW around `v`'s outward normal.
        nbrs = sorted(
            neighbours[v],
            key=lambda uid: math.atan2(
                sum((_ico_verts[uid][k] - _ico_verts[v][k]) * t2[k] for k in range(3)),
                sum((_ico_verts[uid][k] - _ico_verts[v][k]) * t1[k] for k in range(3)),
            ),
        )
        out.append([_edge_cut(v, u, edge_cut)[0] for u in nbrs])
    return out


# --------------------------------------------------------------------- tiles
TILE: float = 0.125  # 128x128 / (16 px per tile) = 8 tiles per row = 0.125 in UV


def _tile_grid(
    row_count: int,
    col_count: int,
    row_offset: int = 0,
) -> list[tuple[float, float, float, float]]:
    """Generate a rectangular grid of UV tiles of size ``TILE``."""
    return [
        (c * TILE, (row_offset + r) * TILE, (c + 1) * TILE, (row_offset + r + 1) * TILE)
        for r in range(row_count)
        for c in range(col_count)
    ]


# ---------------------------------------------------------------------- main
def build_football() -> Model:
    """Build the football :class:`Model` (truncated icosahedron)."""
    all_verts, edge_cut = _truncate_edges()

    hexagons = [ensure_outward(h, all_verts) for h in _hexagons(edge_cut)]
    pentagons = [ensure_outward(p, all_verts) for p in _pentagons(edge_cut, all_verts)]
    assert len(hexagons) == 20
    assert len(pentagons) == 12

    pent_tiles = _tile_grid(row_count=3, col_count=4)
    hex_tiles = _tile_grid(row_count=4, col_count=5, row_offset=4)

    faces: list[Face] = []
    # 12 pentagons, black.
    for i, vids in enumerate(pentagons):
        faces.append(
            Face(
                vertex_ids=vids,
                uvs=project_uv(vids, all_verts, pent_tiles[i]),
                color=0,
            ),
        )
    # 20 hexagons, white.
    for i, vids in enumerate(hexagons):
        faces.append(
            Face(
                vertex_ids=vids,
                uvs=project_uv(vids, all_verts, hex_tiles[i]),
                color=1,
            ),
        )

    flat_verts: list[float] = [c for v in all_verts for c in v]
    mesh = Mesh(name="icosahedron", vertices=flat_verts, faces=faces)
    node = Node(name="football", mesh=mesh)
    root = Node(name="root", children=[node])

    tex = Texture(background_color=1)
    for tile in pent_tiles:
        tex.paint_tile(tile, 0)

    return Model(
        root=root,
        texture=tex,
        camera=Camera(
            pos=(3.0, 2.0, 3.0),
            target=(0.0, 0.0, 0.0),
            distance_to_target=4.36,
            omega=-1.575,
            theta=0.55,
        ),
    )


def main() -> None:
    """Write ``models/football.txt``."""
    model = build_football()
    out_path = Path(__file__).resolve().parent.parent / "models" / "football.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.write(out_path)
    print(f"wrote {out_path}")
    print(
        f"verts=60 faces={len(model.root.children[0].mesh.faces)} "  # type: ignore[union-attr]
        f"pent=12 hex=20",
    )


if __name__ == "__main__":
    main()
