"""Dataclasses and JSON serializer for picoCAD 2 model files.

The shape mirrors the on-disk JSON exactly:

    metadata / texture / graph
        graph.children[*].mesh.{vertices, faces}
        graph.children[*].transform.{pos, rot, scale}
        graph.children[*].motions.tracks  (4 per node)

Invariants enforced by this module (so recipes cannot silently produce
unloadable files):

* ``vertex_ids`` are 1-BASED -- picoCAD stores vertices in a Lua table, so
  index 0 is ``nil`` and crashes ``scene.lua:456`` on load. Pass 0-based
  indices to :class:`Face` and the serializer shifts them for you.
* ``colors`` always has 16 entries; ``shade_pal_1/2`` each have 16.
* ``texture.pixels`` is always exactly 16384 hex chars (128x128).
* Every :class:`Node` carries 4 motion tracks (picoCAD writes 4 even when
  empty; omitting them would corrupt the animation panel state).
* Output is ASCII-only -- non-ASCII characters break GIF export per the
  picoCAD manual.

The serializer (``Model.write``) raises ``ValueError`` if any of these
invariants are violated.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .palette import (
    DEFAULT_BACKGROUND_COLOR,
    DEFAULT_COLORS,
    DEFAULT_SHADE_PAL_1,
    DEFAULT_SHADE_PAL_2,
    DEFAULT_TRANSPARENT_COLOR,
)
from .texture import Texture

if TYPE_CHECKING:
    from pathlib import Path

__all__ = [
    "UV",
    "Camera",
    "ExportSettings",
    "Face",
    "Mesh",
    "Model",
    "Node",
    "SpritesheetSettings",
    "Transform",
    "Vec3",
]

type Vec3 = tuple[float, float, float]
type UV = list[float]  # flat [u0, v0, u1, v1, ...] pairs


@dataclass(slots=True)
class Face:
    """A single polygon face on a :class:`Mesh`.

    Parameters
    ----------
    vertex_ids
        Vertex indices into the parent mesh's ``vertices`` list. Pass them
        **0-based** from the recipe; the serializer shifts to 1-based.
    uvs
        Flat ``[u0, v0, u1, v1, ...]`` UV pairs, one per vertex, in the
        same order as ``vertex_ids``. Length must equal ``2 * len(vertex_ids)``.
    color
        Palette index (0..15) used when the face is non-textured.
    dbl
        Optional "double-sided" flag. ``None`` omits the key from the JSON
        so picoCAD picks its own default.
    """

    vertex_ids: list[int]
    uvs: list[float]
    color: int = 0
    dbl: bool | None = None


@dataclass(slots=True)
class Mesh:
    """A picoCAD mesh: a flat vertex array plus a list of :class:`Face`.

    Parameters
    ----------
    name
        Primitive name shown in picoCAD's UI (e.g. ``"cube"``).
    vertices
        Flat ``[x0, y0, z0, x1, y1, z1, ...]`` list. Number of vertices
        equals ``len(vertices) // 3``.
    faces
        Faces referencing into ``vertices`` (0-based indices).
    """

    name: str
    vertices: list[float]
    faces: list[Face] = field(default_factory=list)

    def to_json(self) -> dict[str, object]:
        """Serialise to the dict picoCAD expects under ``graph.*.mesh``."""
        faces_out: list[dict[str, object]] = []
        for face in self.faces:
            f: dict[str, object] = {
                # 1-based shift: picoCAD stores verts in a Lua table.
                "vertex_ids": [v + 1 for v in face.vertex_ids],
                "uvs": list(face.uvs),
                "color": face.color,
            }
            if face.dbl is not None:
                f["dbl"] = face.dbl
            faces_out.append(f)
        return {
            "name": self.name,
            "vertices": list(self.vertices),
            "faces": faces_out,
        }


@dataclass(slots=True)
class Transform:
    """A node's rest-pose transform (``pos`` + ``rot`` + ``scale``).

    Rotation values are radians (picoCAD stores whatever you give it; the
    editor works in radians internally).
    """

    pos: Vec3 = (0.0, 0.0, 0.0)
    rot: Vec3 = (0.0, 0.0, 0.0)
    scale: Vec3 = (1.0, 1.0, 1.0)

    def to_json(self) -> dict[str, dict[str, float]]:
        """Serialise to the nested ``{pos:{x,y,z}, ...}`` dict picoCAD expects."""
        return {
            "pos": {"x": self.pos[0], "y": self.pos[1], "z": self.pos[2]},
            "rot": {"x": self.rot[0], "y": self.rot[1], "z": self.rot[2]},
            "scale": {"x": self.scale[0], "y": self.scale[1], "z": self.scale[2]},
        }


@dataclass(slots=True)
class Node:
    """A scene-graph node.

    A node with ``mesh`` set is a leaf mesh; a node without ``mesh`` is a
    folder. Folders can be merged into a single mesh from picoCAD's project
    overview (right-click → "merge"); on disk they remain per-node meshes.
    """

    name: str
    mesh: Mesh | None = None
    children: list[Node] = field(default_factory=list)
    transform: Transform = field(default_factory=Transform)
    motions_tracks: tuple[list[object], list[object], list[object], list[object]] = (
        [],
        [],
        [],
        [],
    )
    visible: bool = True
    open: bool = False
    locked: bool = False

    def to_json(self) -> dict[str, object]:
        """Recursively serialise this node and its children."""
        out: dict[str, object] = {
            "motions": {"tracks": [list(t) for t in self.motions_tracks]},
            "children": [c.to_json() for c in self.children],
            "visible": self.visible,
            "name": self.name,
            "open": self.open,
            "locked": self.locked,
            "transform": self.transform.to_json(),
        }
        if self.mesh is not None:
            out["mesh"] = self.mesh.to_json()
        return out


@dataclass(slots=True)
class Camera:
    """3D viewport camera state saved with the model.

    The ``bookmark`` saved with the camera is a copy of the main camera
    (picoCAD's "reset on SHIFT-click" point), which is enough for recipes.
    """

    pos: Vec3 = (3.0, 2.0, 3.0)
    target: Vec3 = (0.0, 0.0, 0.0)
    distance_to_target: float = 4.36
    omega: float = -1.575
    theta: float = 0.55

    def to_json(self) -> dict[str, object]:
        """Serialise to the camera dict picoCAD expects under ``metadata.camera``."""
        base: dict[str, object] = {
            "pos": {"x": self.pos[0], "y": self.pos[1], "z": self.pos[2]},
            "target": {"x": self.target[0], "y": self.target[1], "z": self.target[2]},
            "distance_to_target": self.distance_to_target,
            "omega": self.omega,
            "theta": self.theta,
        }
        base["bookmark"] = {
            "pos": {"x": self.pos[0], "y": self.pos[1], "z": self.pos[2]},
            "target": {"x": self.target[0], "y": self.target[1], "z": self.target[2]},
            "distance_to_target": self.distance_to_target,
            "omega": self.omega,
            "theta": self.theta,
        }
        return base


@dataclass(slots=True)
class ExportSettings:
    """Last-used GIF export settings (persisted into ``metadata.export_settings``)."""

    speed: int = 5
    anim: str = "spin"
    size: int = 128
    outline_color: int = 0
    outline_size: int = 0
    scanline_color: int = 0
    scanlines: bool = False
    watermark: str = "#picoCAD2"
    watermark2: str = ""
    scale: int = 3
    dir: int = -1

    def to_json(self) -> dict[str, object]:
        """Serialise to the dict picoCAD persists per-model."""
        return {
            "speed": self.speed,
            "anim": self.anim,
            "size": self.size,
            "outline_color": self.outline_color,
            "outline_size": self.outline_size,
            "scanline_color": self.scanline_color,
            "scanlines": self.scanlines,
            "watermark": self.watermark,
            "watermark2": self.watermark2,
            "scale": self.scale,
            "dir": self.dir,
        }


@dataclass(slots=True)
class SpritesheetSettings:
    """Last-used sprite-sheet export settings."""

    frame_width: int = 48
    num_frames: int = 8
    cam_dist: float = 4.0
    cam_target_y: float = 0.0
    cam_theta: float = 0.3
    cam_ortho: bool = True

    def to_json(self) -> dict[str, object]:
        """Serialise to the dict picoCAD persists per-model."""
        return {
            "frame_width": self.frame_width,
            "num_frames": self.num_frames,
            "cam_dist": self.cam_dist,
            "cam_target_y": self.cam_target_y,
            "cam_theta": self.cam_theta,
            "cam_ortho": self.cam_ortho,
        }


@dataclass
class Model:
    """A complete picoCAD 2 model: scene graph + texture + palette + metadata.

    The `Model` is the root entry point for serialisation. Recipes build a
    :class:`Node` tree of :class:`Mesh` instances plus a :class:`Texture`,
    then call :meth:`write` to emit a picoCAD-loadable ``*.txt`` file.

    Defaults are chosen so a freshly-constructed ``Model`` loads cleanly
    in picoCAD: 16-color neutral palette, transparent slot unused, identity
    root transform, default 3D viewport camera, and standard GIF/sprite-
    sheet export settings.
    """

    root: Node
    texture: Texture
    colors: list[tuple[float, float, float]] = field(
        default_factory=lambda: [(c[0], c[1], c[2]) for c in DEFAULT_COLORS],
    )
    shade_pal_1: list[int] = field(default_factory=lambda: list(DEFAULT_SHADE_PAL_1))
    shade_pal_2: list[int] = field(default_factory=lambda: list(DEFAULT_SHADE_PAL_2))
    transparent_color: int = DEFAULT_TRANSPARENT_COLOR
    background_color: int = DEFAULT_BACKGROUND_COLOR
    motion_duration: int = 2
    shading_mode: int = 1
    face_mode: int = 2
    camera: Camera = field(default_factory=Camera)
    export_settings: ExportSettings = field(default_factory=ExportSettings)
    spritesheet_settings: SpritesheetSettings = field(
        default_factory=SpritesheetSettings,
    )
    version: str = "2.0"

    def to_json(self) -> dict[str, object]:
        """Build the full JSON dict picoCAD expects at the top level of a file."""
        return {
            "metadata": {
                "version": self.version,
                "motion_duration": self.motion_duration,
                "shading_mode": self.shading_mode,
                "face_mode": self.face_mode,
                "camera": self.camera.to_json(),
                "export_settings": self.export_settings.to_json(),
                "spritesheet_settings": self.spritesheet_settings.to_json(),
            },
            "texture": {
                "colors": [list(c) for c in self.colors],
                "pixels": self.texture.to_hex(),
                "shade_pal_1": list(self.shade_pal_1),
                "shade_pal_2": list(self.shade_pal_2),
                "transparent_color": self.transparent_color,
                "background_color": self.background_color,
            },
            "graph": self.root.to_json(),
        }

    def write(self, path: str | Path, *, indent: int = 2) -> None:
        """Serialise the model to a picoCAD-loadable ``*.txt`` JSON file.

        Parameters
        ----------
        path
            Output file path. The file is written with ``encoding="ascii"``
            because non-ASCII characters in paths/watermarks break picoCAD
            GIF export (per the manual).
        indent
            JSON indentation. ``2`` matches picoCAD's own output style.

        Raises
        ------
        ValueError
            If any format invariant is violated (16 colors, 16 shade
            entries each, 16384-pixel texture).
        """
        # Validate invariants before touching disk.
        self.validate()

        with open(path, "w", encoding="ascii") as f:
            json.dump(self.to_json(), f, indent=indent)

    def validate(self) -> None:
        """Check all picoCAD file-format invariants.

        Raises
        ------
        ValueError
            On any violation, with a message naming the offending field.
        """
        if len(self.colors) != 16:
            raise ValueError(f"colors must have 16 entries, got {len(self.colors)}")
        if len(self.shade_pal_1) != 16:
            raise ValueError(
                f"shade_pal_1 must have 16 entries, got {len(self.shade_pal_1)}",
            )
        if len(self.shade_pal_2) != 16:
            raise ValueError(
                f"shade_pal_2 must have 16 entries, got {len(self.shade_pal_2)}",
            )
        # ``Texture.to_hex`` itself enforces the 16384-length invariant,
        # but call it once here so errors surface before disk I/O.
        _ = self.texture.to_hex()
