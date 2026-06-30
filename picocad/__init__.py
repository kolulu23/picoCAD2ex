"""Reusable, model-agnostic toolkit for authoring picoCAD 2 model files.

Nothing in this package knows what a football is -- it only knows the file
format (JSON skeleton, 128x128 texture, 16-color palette, 1-based
``vertex_ids``, 4 animation tracks per node, etc.).

Modules
-------
model   : Dataclasses for :class:`Mesh`, :class:`Face`, :class:`Node`,
    :class:`Model` and the JSON serializer that writes a picoCAD-loadable
    ``*.txt`` file. Format invariants are enforced here.
uv      : Geometry helpers (face normal, outward winding, planar UV
    projection into a texture tile).
texture : :class:`Texture` paints tile rectangles and compiles the
    16384-character hex ``pixels`` string.
palette : Default 16-color palette and gray shading ramps.

Usage
-----
A "recipe" script supplies vertices, faces, a tile layout, and optional
palette overrides, then calls :meth:`Model.write` ::

    from picocad.model import Model, Node, Mesh, Face
    from picocad.texture import Texture
    from picocad.uv import project_uv

    mesh = Mesh(name="cube", vertices=[...], faces=[Face(...), ...])
    root = Node(name="root", children=[Node(name="body", mesh=mesh)])
    tex = Texture(background_color=1)
    Model(root=root, texture=tex).write("models/cube.txt")
"""

from .model import (
    Camera,
    ExportSettings,
    Face,
    Mesh,
    Model,
    Node,
    SpritesheetSettings,
    Transform,
)
from .palette import (
    DEFAULT_BACKGROUND_COLOR,
    DEFAULT_COLORS,
    DEFAULT_SHADE_PAL_1,
    DEFAULT_SHADE_PAL_2,
    DEFAULT_TRANSPARENT_COLOR,
)
from .texture import SIZE as TEXTURE_SIZE
from .texture import Texture
from .uv import basis, cross, dot, ensure_outward, face_normal, normalize, project_uv, sub

__all__ = [
    # palette
    "DEFAULT_BACKGROUND_COLOR",
    "DEFAULT_COLORS",
    "DEFAULT_SHADE_PAL_1",
    "DEFAULT_SHADE_PAL_2",
    "DEFAULT_TRANSPARENT_COLOR",
    # texture
    "TEXTURE_SIZE",
    # model
    "Camera",
    "ExportSettings",
    "Face",
    "Mesh",
    "Model",
    "Node",
    "SpritesheetSettings",
    "Texture",
    "Transform",
    # uv
    "basis",
    "cross",
    "dot",
    "ensure_outward",
    "face_normal",
    "normalize",
    "project_uv",
    "sub",
]
