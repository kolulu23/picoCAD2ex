"""Recipe: build a unit cube model using the picocad toolkit.

Run::

    uv run python scripts/gen_cube.py

Outputs ``models/cube.txt``.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from picocad.model import Face, Mesh, Model, Node, Transform
from picocad.texture import Texture
from picocad.uv import ensure_outward, project_uv

if TYPE_CHECKING:
    from collections.abc import Sequence

# Type aliases local to this recipe.
Verts = list[float]
FaceSpec = tuple[list[int], int]  # (vertex_ids, palette color)


def build_cube() -> Model:
    """Construct a unit cube ``Model`` centred at the origin.

    Returns
    -------
    Model
        A 6-quad cube, each face planar-UV-mapped onto a 32x32 pixel tile
        and color-coded by palette index.
    """
    vertices: Verts = [
        -0.5,
        -0.5,
        -0.5,  # 0
        0.5,
        -0.5,
        -0.5,  # 1
        0.5,
        0.5,
        -0.5,  # 2
        -0.5,
        0.5,
        -0.5,  # 3
        -0.5,
        -0.5,
        0.5,  # 4
        0.5,
        -0.5,
        0.5,  # 5
        0.5,
        0.5,
        0.5,  # 6
        -0.5,
        0.5,
        0.5,  # 7
    ]
    # Index the flat list into Vec3 triples for the geometry helpers.
    all_verts: Sequence[Sequence[float]] = [
        vertices[i * 3 : i * 3 + 3] for i in range(8)
    ]

    face_specs: list[FaceSpec] = [
        ([0, 1, 2, 3], 0),  # back  -z
        ([5, 4, 7, 6], 1),  # front +z
        ([4, 0, 3, 7], 2),  # left  -x
        ([1, 5, 6, 2], 3),  # right +x
        ([3, 2, 6, 7], 4),  # top   +y
        ([4, 5, 1, 0], 5),  # bottom -y
    ]

    # 3x2 tile grid on the texture, each tile 32x32 px (0.25 in UV).
    tile = 0.25
    tiles = [
        (0, 0, tile, tile),
        (tile, 0, 2 * tile, tile),
        (2 * tile, 0, 3 * tile, tile),
        (0, tile, tile, 2 * tile),
        (tile, tile, 2 * tile, 2 * tile),
        (2 * tile, tile, 3 * tile, 2 * tile),
    ]

    faces: list[Face] = []
    for (vids, color), tile_rect in zip(face_specs, tiles, strict=True):
        vids = ensure_outward(vids, all_verts)
        faces.append(
            Face(
                vertex_ids=vids,
                uvs=project_uv(vids, all_verts, tile_rect),
                color=color,
            ),
        )

    mesh = Mesh(name="cube", vertices=vertices, faces=faces)
    node = Node(name="cube", mesh=mesh, transform=Transform())
    root = Node(name="root", children=[node])

    texture = Texture(background_color=1)
    for (_, color), tile_rect in zip(face_specs, tiles, strict=True):
        texture.paint_tile(tile_rect, color)

    return Model(root=root, texture=texture)


def main() -> None:
    """Entry point: build the cube and write it to ``models/cube.txt``."""
    model = build_cube()
    out_path = Path(__file__).resolve().parent.parent / "models" / "cube.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.write(out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
