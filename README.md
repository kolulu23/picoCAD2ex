# picoCAD 2 — authoring toolkit & recipes

Reusable, model-agnostic toolkit for writing [picoCAD 2] model `*.txt`
files by hand or procedurally. The `picocad` package knows only the file
format; per-model "recipe" scripts supply the geometry.

![football demo](assets/football.gif)

*Rendered from `models/football.txt` produced by
`scripts/gen_football.py` — a 32-face truncated icosahedron, 12 black
pentagons + 20 white hexagons, planar-UV-mapped onto a 128×128 texture.*

## Layout

```
picocad/               # reusable toolkit (model-agnostic, importable)
├── __init__.py        #   re-exports the public API
├── model.py           #   Mesh/Face/Node/Model dataclasses + JSON serializer
├── uv.py              #   ensure_outward(), project_uv() — any mesh
├── texture.py         #   Texture.paint_tile() → 128x128 hex string
└── palette.py         #   default 16-color palette + shade ramps
scripts/               # runnable recipe scripts (not imported by the lib)
├── gen_football.py    #   truncated icosahedron (12 pent / 20 hex)
└── gen_cube.py        #   unit cube
tests/                 # pytest suite
└── test_smoke.py      #   asserts file-format invariants on a built model
examples/              # real picoCAD 2 v2.0 sample models (read-only refs)
assets/                # rendered previews checked into the repo
.agents/skills/        # opencode skills (picocad2-edit, picocad2-manual)
```

## Why flat layout

`picocad/` lives at the project root (not under `src/` or `scripts/`) so
`import picocad` resolves the same way whether installed via `uv sync`
or invoked in-place. Recipe scripts no longer need `sys.path` hacks.

## Requirements

- Python ≥ 3.12 (uses modern `type` aliases, `X | None`, `slots=True`).
- [uv] for environment management (optional; runtime deps are stdlib-only).

## Quick start (uv)

```powershell
uv sync                      # creates .venv with Python 3.12, installs dev deps
uv run python scripts/gen_football.py
uv run python scripts/gen_cube.py
uv run pytest                # 8 invariant tests
uv run ruff check picocad scripts tests   # lint
uv run ruff format picocad scripts tests  # format
uv run mypy                  # strict typecheck
```

## Quick start (plain Python 3.12, no uv)

```powershell
python -m pip install pytest ruff mypy
python scripts/gen_football.py
python scripts/gen_cube.py
python -m pytest
```

## File-format invariants the toolkit enforces

- `vertex_ids` are **1-based** (picoCAD stores vertices in a Lua table;
  index 0 → `nil` → `scene.lua:456` crash on load).
- `colors` always has 16 entries; `shade_pal_1/2` each have 16.
- `texture.pixels` is always exactly 16384 hex chars (128x128).
- Every `Node` carries 4 motion tracks (picoCAD writes 4 even when empty).
- Output is ASCII-only (non-ASCII breaks GIF export per picoCAD manual).

For the full canonical schema with example snippets, cardinality tables,
and known conflicts (real files vs. manual-skill claims), see
[`.agents/skills/picocad2-edit/SCHEMA.md`](.agents/skills/picocad2-edit/SCHEMA.md).
Real picoCAD-saved reference models live under [`examples/`](examples/) —
use them as ground truth when in doubt.

## Writing a new recipe

```python
from picocad.model import Model, Node, Mesh, Face, Transform, Camera
from picocad.texture import Texture
from picocad.uv import ensure_outward, project_uv
from pathlib import Path

# 1. supply verts (flat xyz) and faces (0-based vertex indices)
vertices = [x0, y0, z0, x1, y1, z1, ...]
face_specs = [([0, 1, 2, 3], 0), ...]       # (vids, palette color)

# 2. per-face UVs via project_uv, assemble into Mesh, wrap in Node
faces = [...]
mesh = Mesh(name="my-model", vertices=vertices, faces=faces)
root = Node(name="root", children=[Node(name="body", mesh=mesh)])

# 3. paint texture tiles + serialise
texture = Texture(background_color=1)
Model(root=root, texture=texture).write(Path("models/my-model.txt"))
```

Drop the new file into `scripts/gen_<thing>.py`; no edits to `picocad/`
or `pyproject.toml` are needed.

[picoCAD 2]: https://picocad.net
[uv]: https://docs.astral.sh/uv/