"""Geometry helpers shared by any picoCAD generator.

All functions are pure -- they take coordinates and return coordinates,
with no dependency on the rest of the toolkit. They are safe to reuse
outside picoCAD (for example when crafting UVs by hand for another tool).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

__all__ = [
    "Vec3",
    "basis",
    "cross",
    "dot",
    "ensure_outward",
    "face_normal",
    "normalize",
    "project_uv",
    "sub",
]

# A 3D point or vector. ``Sequence[float]`` keeps the helpers duck-typed
# so callers can pass tuples, lists, or numpy slices without conversion.
Vec3 = Sequence[float]


def normalize(v: Vec3) -> list[float]:
    """Return the unit vector along ``v``.

    Zero vectors return ``[0.0, 0.0, 0.0]`` rather than raising -- handy
    when degenerate faces slip through and shouldn't take down a build.
    """
    length = math.sqrt(float(v[0]) ** 2 + float(v[1]) ** 2 + float(v[2]) ** 2)
    if length == 0.0:
        return [0.0, 0.0, 0.0]
    return [float(v[0]) / length, float(v[1]) / length, float(v[2]) / length]


def sub(a: Vec3, b: Vec3) -> list[float]:
    """Return ``a - b`` component-wise."""
    return [float(a[0]) - float(b[0]), float(a[1]) - float(b[1]), float(a[2]) - float(b[2])]


def cross(a: Vec3, b: Vec3) -> list[float]:
    """Return the cross product ``a x b``."""
    return [
        float(a[1]) * float(b[2]) - float(a[2]) * float(b[1]),
        float(a[2]) * float(b[0]) - float(a[0]) * float(b[2]),
        float(a[0]) * float(b[1]) - float(a[1]) * float(b[0]),
    ]


def dot(a: Vec3, b: Vec3) -> float:
    """Return the dot product ``a . b``."""
    return float(a[0]) * float(b[0]) + float(a[1]) * float(b[1]) + float(a[2]) * float(b[2])


def face_normal(verts: Iterable[Vec3]) -> list[float]:
    """Normal of the plane defined by the first three vertices of ``verts``.

    Returned vector is **not** normalised -- its magnitude scales with the
    area of the triangle, which is occasionally useful for weighting. Use
    :func:`normalize` if you need a unit vector.

    Raises
    ------
    ValueError
        If fewer than three vertices are supplied.
    """
    it = iter(verts)
    try:
        a = next(it)
        b = next(it)
        c = next(it)
    except StopIteration as exc:
        raise ValueError("face_normal needs at least 3 vertices") from exc
    return cross(sub(b, a), sub(c, a))


def basis(n: Vec3) -> tuple[list[float], list[float]]:
    """Return two unit vectors ``(t1, t2)`` perpendicular to ``n``.

    Together with the normalised ``n`` they form a right-handed orthonormal
    basis, used by :func:`project_uv` to drop a face's 3D vertices onto a
    2D texture plane. The choice of reference up avoids the degenerate
    case where ``n`` is parallel to the z-axis.
    """
    n_unit = normalize(n)
    ref = [0.0, 0.0, 1.0] if abs(n_unit[2]) < 0.9 else [1.0, 0.0, 0.0]
    t1 = normalize([ref[k] - dot(ref, n_unit) * n_unit[k] for k in range(3)])
    t2 = cross(n_unit, t1)
    return t1, t2


def ensure_outward(vids: Sequence[int], all_verts: Sequence[Vec3]) -> list[int]:
    """Reverse ``vids`` if the face winds inward.

    A face winds inward when its normal points toward the origin (the face's
    own centroid tents in against its normal). This is the right heuristic
    for any convex mesh centred at the origin. For offset or parented
    meshes, transform ``all_verts`` into world space first.

    Parameters
    ----------
    vids
        Vertex indices (0-based or 1-based -- only used to index
        ``all_verts``, so be consistent).
    all_verts
        Pool of vertices that ``vids`` references.

    Returns
    -------
    list[int]
        ``vids`` either as-is or reversed, copied so the caller can mutate
        freely without surprising the caller's container.
    """
    face_verts = [all_verts[v] for v in vids]
    normal = face_normal(face_verts)
    centroid = [sum(v[k] for v in face_verts) / len(face_verts) for k in range(3)]
    if dot(normal, centroid) < 0:
        return list(reversed(vids))
    return list(vids)


def project_uv(
    vids: Sequence[int],
    all_verts: Sequence[Vec3],
    tile: tuple[float, float, float, float],
    *,
    inset: float = 0.15,
) -> list[float]:
    """Planar-project ``vids`` into texture ``tile``.

    The face's normal defines the projection plane; the two basis vectors
    perpendicular to it (see :func:`basis`) become the texture's U and V
    axes. The face's 2D bounding box on that plane is stretched to fill the
    tile, then inset by ``inset`` (default 15%) so neighbouring tiles never
    bleed into each other under picoCAD's affine mapping.

    Parameters
    ----------
    vids
        Vertex indices into ``all_verts`` (any consistent indexing -- the
        function only reads ``all_verts[vi]``).
    all_verts
        Pool of vertices indexed by ``vids``.
    tile
        ``(u0, v0, u1, v1)`` in UV space ``[0, 1]``. ``[0, 0]`` is the
        top-left of the texture image, matching picoCAD.
    inset
        Fraction of the tile to leave empty on each side. ``0.0`` fills
        edge to edge; ``0.15`` is a safe default for 128x128 textures.

    Returns
    -------
    list[float]
        Flat ``[u0, v0, u1, v1, ...]`` list of UV pairs, one pair per
        vertex, in the same order as ``vids``.
    """
    normal = face_normal([all_verts[v] for v in vids])
    t1, t2 = basis(normal)

    projected = [(dot(all_verts[v], t1), dot(all_verts[v], t2)) for v in vids]
    min_a = min(p[0] for p in projected)
    max_a = max(p[0] for p in projected)
    min_b = min(p[1] for p in projected)
    max_b = max(p[1] for p in projected)

    u0, v0, u1, v1 = tile
    tile_w = u1 - u0
    tile_h = v1 - v0
    span_a = max_a - min_a if (max_a - min_a) > 1e-9 else 1.0
    span_b = max_b - min_b if (max_b - min_b) > 1e-9 else 1.0
    inner_w = (1.0 - 2 * inset) * tile_w
    inner_h = (1.0 - 2 * inset) * tile_h

    uvs: list[float] = []
    for a, b in projected:
        un = (a - min_a) / span_a
        vn = (b - min_b) / span_b
        uvs.append(u0 + inset * tile_w + inner_w * un)
        uvs.append(v0 + inset * tile_h + inner_h * vn)
    return uvs
