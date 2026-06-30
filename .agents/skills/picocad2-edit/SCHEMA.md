# picoCAD 2 Model File Schema (v2.0)

A **formal, agent-friendly** reference for the canonical `*.txt` model file
format used by picoCAD 2. Ground truth = the real picoCAD-saved files in
`examples/` (`pig.txt`, `pirate.txt`, `waterfall.txt`, `rig.txt`,
`livingroom.txt`, `advanced_meshes.txt`), cross-checked against the
official manual at <https://picocad.net/manual/> and against the invariants
enforced by the local Python toolkit in `picocad/`.

> **Authoritative sources, in priority order:**
> 1. The real model files in `examples/` (picoCAD-saved, v2.0).
> 2. The `picocad/` Python toolkit's enforced invariants (`model.Model.validate`).
> 3. The official manual (workflow/UI claims) — *only* where it does not
>    conflict with #1.
>
> If anything in another doc (e.g. the `picocad2-manual` skill's clip-object
> notes) conflicts with what real picoCAD-saved files do, **the files win.**
> Known conflicts are flagged inline as **[CONFLICT]**.

A software update may invalidate parts of this document. When you edit a
file, re-validate with `uv run pytest` (parses/round-trips a built model)
and by loading it in picoCAD itself.

---

## 0. Quick output contract (what a valid file looks like)

A minimal loadable model file is a UTF-8/ASCII JSON object with **exactly
three top-level keys**: `texture`, `graph`, `metadata` (any order). The
absolute hard invariants are:

| Invariant                                                            | Source            |
|----------------------------------------------------------------------|-------------------|
| `texture.colors` has exactly 16 RGB triples (floats 0..1)            | `Model.validate`  |
| `texture.shade_pal_1` has exactly 16 ints                            | `Model.validate`  |
| `texture.shade_pal_2` has exactly 16 ints                            | `Model.validate`  |
| `texture.pixels` is exactly **16384** hex chars                       | `Texture.to_hex`  |
| `texture.transparent_color` ∈ 0..15                                  | examples          |
| `texture.background_color`  ∈ 0..15                                  | examples          |
| Every node has `motions.tracks`, a 4-element array                   | `Model.validate`  |
| `vertex_ids` are **1-based** (id 0 → Lua `nil` → load crash)          | `picocad/model.py`|
| `face.uvs` length == `2 * len(face.vertex_ids)`                       | `test_smoke.py`   |
| `face.vertex_ids` length 3..8 (n-gons up to 8 corners)               | examples          |
| File is ASCII (non-ASCII breaks GIF export)                          | manual            |

### Minimal loadable example (≈ one unit cube)

```json
{
  "texture": {
    "transparent_color": 14,
    "background_color": 1,
    "colors": [[0,0,0],[1,1,1],[0.78,0.78,0.80],[0.55,0.55,0.57],
               [0.30,0.30,0.32],[0.20,0.20,0.22],[0.65,0.65,0.67],
               [0.85,0.85,0.87],[0.60,0.60,0.62],[0.90,0.90,0.92],
               [0.95,0.95,0.95],[0.92,0.92,0.94],[0.50,0.50,0.52],
               [0.40,0.40,0.42],[1,1,1],[0.97,0.97,0.99]],
    "shade_pal_1": [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
    "shade_pal_2": [0,2,3,4,5,5,6,7,8,9,10,11,12,13,14,15],
    "pixels": "1111111111111111...<16384 chars total>...1111111111111111"
  },
  "graph": {
    "name":"root","visible":true,"open":false,"locked":false,
    "transform":{"pos":{"x":0,"y":0,"z":0},"rot":{"x":0,"y":0,"z":0},"scale":{"x":1,"y":1,"z":1}},
    "motions":{"tracks":[[],[],[],[]]},
    "children":[{
      "name":"cube","visible":true,"open":false,"locked":false,
      "transform":{"pos":{"x":0,"y":0,"z":0},"rot":{"x":0,"y":0,"z":0},"scale":{"x":1,"y":1,"z":1}},
      "motions":{"tracks":[[],[],[],[]]},
      "children":[],
      "mesh":{
        "name":"cube",
        "vertices":[-0.5,-0.5,-0.5, 0.5,-0.5,-0.5, 0.5,0.5,-0.5, -0.5,0.5,-0.5,
                    -0.5,-0.5,0.5,  0.5,-0.5,0.5,  0.5,0.5,0.5,   -0.5,0.5,0.5],
        "faces":[
          {"color":1,"vertex_ids":[5,6,2,1],"uvs":[0,0.25, 0.25,0.25, 0.25,0, 0,0]},
          {"color":1,"vertex_ids":[1,2,3,4],"uvs":[0,0.25, 0.25,0.25, 0.25,0, 0,0]}
        ]
      }
    }]
  },
  "metadata":{
    "version":"2.0",
    "motion_duration":2,
    "shading_mode":1,
    "face_mode":2,
    "camera":{
      "pos":{"x":3,"y":2,"z":3},"target":{"x":0,"y":0,"z":0},
      "distance_to_target":4.36,"omega":-1.575,"theta":0.55,
      "bookmark":{"pos":{"x":3,"y":2,"z":3},"target":{"x":0,"y":0,"z":0},
                  "distance_to_target":4.36,"omega":-1.575,"theta":0.55}
    },
    "spritesheet_settings":{"frame_width":48,"num_frames":8,"cam_dist":4.0,
                            "cam_target_y":0,"cam_theta":0.3,"cam_ortho":true},
    "export_settings":{"anim":"spin","speed":5,"size":128,"scale":3,"dir":-1,
                       "scanlines":false,"scanline_color":0,
                       "outline_size":0,"outline_color":0,
                       "watermark":"#picoCAD2","watermark_color":15,
                       "watermark2":"","watermark2_color":15,
                       "fov_type":"perspective"}
  }
}
```

The toolkit's `Model.write` produces exactly this shape; see
`scripts/gen_cube.py` for a runnable recipe that emits it.

---

## 1. Top-level structure

```json
{
  "texture":  { ... },   // palette + 128x128 indexed-pixel texture image
  "graph":    { ... },   // recursive scene tree (root node)
  "metadata": { ... }    // editor / camera / export / spritesheet state
}
```

All three keys are present in every current (v2.0) example file. JSON object
key order is **not semantic** (e.g. `rig.txt` puts `graph` first; `pig.txt`
puts `texture` first; the toolkit writes `metadata` first — all load fine).
Array order **is** semantic (vertices, faces, uvs, vertex_ids, tracks,
children).

---

## 2. `texture`

```json
"texture": {
  "transparent_color": <int 0..15>,        // palette index treated as fully transparent on render
  "background_color":  <int 0..15>,        // palette index painted behind everything else
  "colors":  [[r,g,b], ... 16 entries],    // 16 RGB triples; r,g,b are floats in 0..1
  "shade_pal_1": [<16 ints>],              // lit-side shade remap table (one entry per palette slot)
  "shade_pal_2": [<16 ints>],              // shadow-side shade remap table
  "pixels": "<16384 hex chars>"            // 128x128 indexed image, row-major, top-to-bottom
}
```

- `colors` is **always exactly 16** RGB triples (verified in all 6 examples
  and enforced by `Model.validate`). Example from `pig.txt`:
  ```json
  "colors":[[0,0,0],[0.11372,0.16862,0.32549], ... ,[1,0.94509,0.90980]]
  ```
- `shade_pal_1` / `shade_pal_2` are **always exactly 16** entries.
  - Most entries are in `0..15` (a palette index to substitute when shaded).
  - The sentinel value **`31`** also appears (e.g. `waterfall.txt`,
    `livingroom.txt`, `pirate.txt`); inference: `31` = "do not remap, keep
    the original color in this slot" (no-shade).
  - Example from `waterfall.txt`:
    ```json
    "shade_pal_1":[0,31,2,2,3,1,5,6,8,8,9,11,11,12,9,14]
    ```
- `pixels` is one contiguous hex string of length `128*128 = 16384`. Each
  character is a single hex digit `0..f` selecting `colors[idx]`. Rows are
  laid out **top-to-bottom**, left-to-right. UV space `[0,1]` × `[0,1]`
  maps to the full 128×128 image with origin in the **top-left** (matches
  picoCAD's texture viewport).

> **[CONFLICT]** the older `picocad2-manual` skill's clip-object section
> claims `pixels` is 4096 chars — that is **wrong**; the real length is
> 16384 (128×128). Verified by parsing every example file.

---

## 3. `graph` — the scene tree

`graph` is the **root scene node**. Every node follows the same shape;
the presence/absence of `mesh` vs `folder` decides its kind.

### 3.1 Node shape

```json
{
  "name":      "<string>",                 // label; root is conventionally "root" (rig.txt omits it)
  "visible":   <bool>,                     // editor visibility toggle
  "open":      <bool>,                     // UI tree-expanded state
  "locked":    <bool>,                     // editor lock flag
  "transform": { ... },                     // local rest-pose transform (see 3.2)
  "motions":   { "tracks": [...] },        // animation tracks, always 4 slots (see 3.3)
  "children":  [ ...node... ],             // child nodes; empty array on leaves

  // EITHER (geometry leaf):
  "mesh":      { ... },                    // present on geometry leaves (see 3.4); implies children: []
  // OR (group):
  "folder":    <bool>                      // present (and true) on group nodes with no mesh
}
```

**Rule (confirmed across all examples):**
- A node carrying `mesh` is a **geometry leaf**: it has `children:[]` and
  no `folder` key.
- A node carrying `"folder":true` is a **group**: it has no `mesh` and
  usually non-empty `children`.
- The root node behaves like a group but in some files (e.g. `rig.txt`)
  omits both `name` and `folder`.

Group example from `waterfall.txt`:
```json
{
  "name":"landscape",
  "folder":true,
  "visible":true,"open":false,"locked":true,
  "transform":{"pos":{"x":0,"y":0,"z":0},
                "scale":{"x":1,"y":1,"z":1},
                "rot":{"x":0,"y":0,"z":0}},
  "motions":{"tracks":[[],[],[],[]]},
  "children":[ ... ]
}
```

Deepest folder nesting in examples: 3 levels (`root → clothes → boots → cube`
in `pirate.txt`). Folder order in `children` === display order in picoCAD's
Project Overview (`O`).

### 3.2 `transform`

```json
"transform": {
  "pos":   {"x":<n>, "y":<n>, "z":<n>},    // local translation
  "scale": {"x":<n>, "y":<n>, "z":<n>},    // local scale (1,1,1 = identity; 0 degenerates)
  "rot":   {"x":<n>, "y":<n>, "z":<n>}      // local rotation, RADIANS (per manual)
}
```

- All three sub-objects are always present, each with `x`,`y`,`z` numeric
  fields. Identity defaults: `pos=(0,0,0)`, `scale=(1,1,1)`, `rot=(0,0,0)`.
- Every `rot` in the example files is `{x:0,y:0,z:0}` — the editor writes
  rotation into the mesh's geometry or into animation clips rather than the
  rest-pose `rot`. The field exists and is load-bearing (the manual says
  radians), but recipes typically leave it at identity.
- `scale` 0 on any axis degenerates the mesh — do not set.

### 3.3 `motions`

```json
"motions": {
  "tracks": [ [], [], [], [] ]    // ALWAYS a 4-element array
}
```

- `tracks` is **always** a 4-element array (one per animation channel/slot),
  enforced by `check_motions` in `tests/test_smoke.py`. An empty track is
  `[]`. A non-empty track is a list of keyframe objects.
- Omitting `motions.tracks` or writing fewer than 4 entries corrupts the
  animation panel state on load.

#### Keyframe (clip) shape

The **only** keyframe shape attested in `examples/` (in `pig.txt`) is:

```json
{
  "prop":   "scale",                   // animated property
  "axises": ["y"],                     // JSON ARRAY of axis names (see conflict note)
  "start":  <num>,                      // start frame
  "stop":   <num>,                      // end frame
  "times":  <int>,                      // repeat count
  "delta":  <num>,                      // per-cycle change applied to the axes
  "icon":   <int>                       // UI icon id (e.g. 470)
}
```

Example from `pig.txt` (3 simultaneous scale clips on one mesh):
```json
"motions":{"tracks":[
  [{"prop":"scale","times":3,"stop":4,"icon":470,"delta":0.1, "start":0,"axises":["y"]}],
  [{"prop":"scale","times":3,"stop":4,"icon":470,"delta":-0.05,"start":0,"axises":["z"]}],
  [{"prop":"scale","times":3,"stop":4,"icon":470,"delta":-0.05,"start":0,"axises":["x"]}],
  []
]}
```

> **[CONFLICT]** the older `picocad2-manual` skill claims `axises` is a
> **space-separated string** (e.g. `"x y"`), and lists extra `prop` values
> (`"rot"`,`"pos"`,`"visibility"`,`"osc"`) plus extra fields (`curve`,
> `pingpong`, `freq`). **None of these are attested in any real
> picoCAD-saved file in `examples/`** — only `"prop":"scale"` and a
> JSON-array `axises` actually appear. Treat all of those additional
> manual-skill claims as **UNVERIFIED**. If you need `rot`/`pos`/visibility
> clips and the editor supports them, the safest path is to create the clip
> in picoCAD, save, and copy the exact shape it wrote. Do **not** invent
> clip shapes from the manual-skill description.

### 3.4 `mesh` (geometry leaves)

```json
"mesh": {
  "name":     "<string>",                 // mesh name; usually matches the node name
  "vertices": [x,y,z, x,y,z, ...],       // FLAT list; vertex k (1-based) = indices [3(k-1)..3(k-1)+2]
  "faces":    [ ...face... ]              // list of polygonal faces
}
```

- `vertices` is a flat numeric array of length `3 * N`. Vertex **k**
  (1-based, as referenced by faces) occupies indices `[3(k-1), 3(k-1)+1, 3(k-1)+2]`.
- Coordinates are arbitrary floats; tiny values like `5.5511151231258e-17`
  appear (mathematical-zero residue) and load fine.
- The MIT `picocad/` **Python toolkit's `Face` dataclass takes 0-based
  indices and shifts to 1-based on write** (`Mesh.to_json`). Hand-edited
  `.txt` files use **1-based** directly.

### 3.5 Face shape

```json
{
  "color":      <int 0..15>,                  // palette index for this face
  "vertex_ids": [<int>, ...],                 // 1-based indices into vertices[]; 3..8 corners
  "uvs":        [<u0>,<v0>, <u1>,<v1>, ...],   // UV per corner; length = 2*len(vertex_ids); values in [0,1]
  "notex":       <bool>,                       // OPTIONAL; true = solid color fill, IGNORE uvs
  "dbl":         <bool>                        // OPTIONAL; true = render double-sided
}
```

- `vertex_ids` length determines face arity. **All of 3, 4, 5, 6, and 8 are
  confirmed** by `examples/advanced_meshes.txt` (triangles, quads,
  dodecahedron pentagons, hex_antiprism hexagons, oct_antiprism octagons).
  7-gons are not attested but the loader clearly accepts variable arity
  up to 8; treat 3..8 as valid.
- `uvs` is a parallel flat list of `2 * corners` floats, packed in corner
  order: `[u0,v0, u1,v1, ...]`. UVs are in `[0,1]` and map to the 128×128
  texture (origin top-left). picoCAD uses PS1-style **affine** mapping, so
  big faces warp strongly — subdivide rather than tweaking UVs.
- `notex` is **optional**. Omitting it = `false` (use the texture, read
  `uvs`). When `notex:true`, the face is filled with the solid palette
  color and `uvs` is ignored (commonly a boilerplate placeholder like
  `[0.375,0,0.5,0,0.5,0.125,0.375,0.125]`). Confirmed in `pirate.txt`,
  `rig.txt`, `pig.txt`.
- `dbl` is **optional**; defaults to `false`. Confirmed across `pig`,
  `pirate`, `waterfall` (fences), `rig`. Use `dbl:true` for thin geometry
  (leaves, fences, capes) where both sides are visible.
- Winding defines the face's forward direction; `picocad.uv.ensure_outward`
  flips winding when the normal faces inward (heuristic for convex meshes
  centered at the origin).

Example with both flags (`pirate.txt`):
```json
{"dbl":true,"color":13,"uvs":[0.75,0.5,0.8125,0.5,0.8125,0.5625,0.75,0.5625],
 "vertex_ids":[6,5,8,7]}
```
Example `notex` face (`rig.txt`):
```json
{"notex":true,"color":3,"uvs":[0.625,0.3125,...],"vertex_ids":[6,5,8,7]}
```

> The older `picocad2-manual` skill also mentions per-face flags `textured`,
> `shaded`, `drawBehind`. **None of these appear in any real
> picoCAD-saved file in `examples/`** (only `notex` and `dbl` do). Treat
> those extra flags as **UNVERIFIED**. The local Python toolkit's `Face`
> dataclass only models `color`, `vertex_ids`, `uvs`, `dbl` — so recipes
> built with the toolkit **cannot** emit `notex:true` without extending the
> dataclass.

---

## 4. `metadata`

Always present in v2.0 files.

```json
"metadata": {
  "version": "2.0",                       // always "2.0" in examples

  "camera": {
    "distance_to_target": <num>,
    "omega": <num>,                       // azimuth (free float; e.g. -13.125 in rig.txt, 0.3 in pirate.txt)
    "theta": <num>,                       // elevation
    "pos":    {"x","y","z"},              // camera position
    "target": {"x","y","z"},              // orbit pivot
    "bookmark": {                         // OPTIONAL saved camera view (any subset of the above)
      "distance_to_target": <num>,
      "omega": <num>, "theta": <num>,
      "pos": {...}, "target": {...}
    }
  },

  "shading_mode": <int 0|1>,              // editor shading mode (0 in livingroom, 1 elsewhere)
  "face_mode":    <int>,                  // editor face display mode (only 2 observed)
  "motion_duration": <int>,              // length of the animation timeline (frames)

  "spritesheet_settings": {
    "frame_width":  <int>,                // output frame size in px (e.g. 48, 64)
    "num_frames":   <int>,                // total frames in the spritesheet
    "cam_dist":     <num>,                // spritesheet camera distance
    "cam_theta":    <num>,                // spritesheet camera elevation
    "cam_target_y": <num>,                // spritesheet target Y offset (can be nonzero)
    "cam_ortho":    <bool>                // true = orthographic camera for the sheet
  },

  "export_settings": {
    "animate":          <bool>,           // OPTIONAL; whether to render an animation
    "anim":             "spin" | "sway",  // animation type (only these two observed)
    "speed":            <num>,            // animation playback speed
    "size":             <int>,            // output image resolution (e.g. 128)
    "scale":            <num>,            // output pixel scale (e.g. 3)
    "fov_type":         "perspective",   // projection (only "perspective" observed, even when cam_ortho:true)
    "dir":              <int>,            // spin direction (e.g. -1)
    "scanlines":        <bool>,           // enable scanline shader
    "scanline_color":   <int 0..15>,      // scanline palette index
    "outline_size":     <int>,            // outline thickness in px (0 = none)
    "outline_color":    <int 0..15>,      // outline palette index
    "watermark":        "<string>",       // primary watermark text (e.g. "#picoCAD2"); ASCII only
    "watermark_color":  <int 0..15>,      // primary watermark palette index
    "watermark2":       "<string>",       // secondary watermark text (often "")
    "watermark2_color": <int 0..15>       // secondary watermark palette index
  }
}
```

Cross-checked facts:
- `export_settings.animate` is **optional**: present in `pig`/`pirate`/`rig`,
  absent in `waterfall`/`livingroom`/`advanced_meshes`. The toolkit's
  `ExportSettings` dataclass does **not** write `animate` (it omits the
  key entirely); recipes therefore produce files without it.
- `export_settings.anim` observed values are exactly `"spin"` and `"sway"`.
  No `"idle"` or other values appear in any example.
- `export_settings.fov_type` is always `"perspective"` even when
  `spritesheet_settings.cam_ortho` is `true`. The two cameras are independent.
- `shading_mode` observed: `0` (livingroom) and `1` (others).
- `face_mode` is `2` in every example; the enum is not otherwise attested.
- `camera.bookmark` may omit fields (`waterfall.txt`'s bookmark omits
  `distance_to_target` and `pos`); it stores whatever the user saved.
- All camera fields can be free floats (no units documented; radians/hermes
  inferred).

Example (`pirate.txt`):
```json
"metadata":{
  "version":"2.0","face_mode":2,
  "camera":{"distance_to_target":20.595667879956,
            "pos":{"x":19.477295412264,"y":8.0823950629069,"z":6.3799505682694},
            "target":{"x":-0.1002006213,"y":6.0262591703276,"z":0.32392136849933},
            "bookmark":{"theta":0.1,"omega":0.3, ... },
            "theta":0.1,"omega":0.3},
  "spritesheet_settings":{"frame_width":64,"num_frames":56,"cam_dist":29,
                          "cam_target_y":5.5,"cam_theta":0.3,"cam_ortho":true},
  "motion_duration":8,
  "export_settings":{"anim":"sway","speed":8,"size":128,"scale":3,
                     "fov_type":"perspective","scanlines":false,
                     "outline_size":0,"outline_color":4,
                     "watermark":"#picoCAD2","watermark_color":15,
                     "watermark2":"","watermark2_color":15,
                     "dir":-1,"animate":true},
  "shading_mode":1
}
```

---

## 5. Cardinality & invariants — quick reference

| Field                              | Required | Type / range                          | Notes |
|------------------------------------|----------|----------------------------------------|-------|
| `texture.colors`                   | yes      | array of exactly 16 `[r,g,b]`          | floats 0..1 |
| `texture.shade_pal_1` / `shade_pal_2` | yes   | array of exactly 16 ints               | values 0..15, or 31 (no-remap sentinel) |
| `texture.pixels`                   | yes      | string of exactly **16384** hex chars  | 128×128 indexed image |
| `texture.transparent_color`        | yes      | int 0..15                              | |
| `texture.background_color`         | yes      | int 0..15                              | |
| `graph.name`                       | usually  | string                                 | root may omit (rig.txt) |
| `graph.transform.{pos,scale,rot}`  | yes      | `{x,y,z}` of numbers                   | rot in radians |
| `graph.motions.tracks`             | yes      | 4-element array of keyframe-arrays     | can be all `[]`; enforced by tests |
| `graph.children`                   | yes      | array of nodes                         | `[]` on leaves |
| `graph.mesh` OR `graph.folder`     | one      | mesh-object OR `true`                  | mutually exclusive |
| `mesh.vertices`                    | yes      | flat array, length = `3 * vertex_count` | floats |
| `mesh.faces[*]`                    | yes      | array of face-objects                  | may be empty |
| face.`vertex_ids`                  | yes      | array of 3..8 ints, **1-based**        | id 0 crashes picoCAD |
| face.`uvs`                         | yes      | array of `2*corners` floats in [0,1]    | ignored when `notex:true` |
| face.`color`                       | yes      | int 0..15                              | |
| face.`notex`                       | no       | bool                                   | default false; true = solid color |
| face.`dbl`                         | no       | bool                                   | default false; true = double-sided |
| keyframe.`prop`                    | yes      | `"scale"` (only attested)              | others UNVERIFIED — see conflict note |
| keyframe.`axises`                  | yes      | **JSON array** of `"x"`/`"y"`/`"z"`    | may contain multiple; NOT a string |
| keyframe.`start`,`stop`,`times`,`delta`,`icon` | yes | number / int            | |
| `metadata.version`                 | yes      | `"2.0"`                                | |
| `metadata.shading_mode`            | yes      | int (0 or 1 observed)                  | |
| `metadata.face_mode`               | yes      | int (only 2 observed)                  | |
| `metadata.motion_duration`         | yes      | int                                    | |
| `metadata.camera`                  | yes      | object                                 | `bookmark` optional inside |
| `metadata.spritesheet_settings`    | yes      | object                                 | |
| `metadata.export_settings`         | yes      | object                                 | `animate` optional inside |
| `metadata.export_settings.animate` | no       | bool                                   | toolkit omits; some app files include it |

---

## 6. Verification workflow (run before declaring done)

This project ships a reusable Python toolkit (`picocad/`) and an invariant
test suite (`tests/`). Use them to confirm любую新建或修改енную model:

```powershell
# 1. Build/round-trip a model with the toolkit (catches invariant violations)
uv run python scripts/gen_cube.py            # a built-in sanity recipe
uv run python scripts/gen_<thing>.py        # your new recipe

# 2. Invariant tests — assert 16 colors, 16-shade ramps, 16384-pixel
#    texture, 1-based vertex_ids, 4 motion tracks per node, UV/vertex count
uv run pytest

# 3. Lint + strict typecheck on any new/changed Python
uv run ruff check picocad scripts tests
uv run ruff format --check picocad scripts tests
uv run mypy                                   # strict, py312
```

For hand-edited `.txt` files (not built via the toolkit), validate by:
1. Parse with `python -c "import json,pathlib; json.loads(pathlib.Path('your.txt').read_text('ascii'))"`.
2. Re-check the §5 cardinality table by hand or with a one-off script
   (count `colors`==16, `pixels` length==16384, every node has 4 tracks,
   every face's `len(uvs)==2*len(vertex_ids)` and `min(vertex_ids)>=1`).
3. Open in picoCAD 2 itself if possible.

---

## 7. Open questions / version caveats

- **`keyframe.prop` values other than `"scale"`** (e.g. `"rot"`, `"pos"`,
  `"visibility"`, `"osc"`): listed by the older `picocad2-manual` skill
  but **not attested** in any local example file. The editor presumably
  supports them, but the on-disk shape (field names like `curve`/`pingpong`/
  `freq`) is UNVERIFIED. If you need them, create the clip in-app, save,
  and copy the exact shape picoCAD wrote.
- **Per-face flags `textured`, `shaded`, `drawBehind`** (from the manual
  skill): not present in any real picoCAD-saved file in `examples/`. Only
  `notex` and `dbl` are attested. UNVERIFIED.
- **`face_mode` enum** values other than `2`: unknown.
- **`export_settings.anim`** values other than `spin`/`sway`: not attested.
- **7-gon faces**: no example contains exactly 7 corners; the loader accepts
  3..8, so 7 is plausibly valid but untested.
- **`shade_pal_* = 31` semantics** ("no remap") is inferred from usage; the
  editor source is not available.
- **`transform.rot` units**: manual says radians; all example values are 0.
  Treat as radians but prefer geometry/clip-based rotation.
- A future picoCAD update may add keys. When you encounter an unfamiliar
  key in a real picoCAD-saved file, preserve it verbatim and add it here.

---

## 8. Where to look for patterns

| Pattern                                | Example file                |
|----------------------------------------|------------------------------|
| Folder nesting (`root → clothes → boots`) | `examples/pirate.txt`     |
| Solid-color faces (`notex:true`)       | `examples/rig.txt`, `examples/pirate.txt` |
| Double-sided faces (`dbl:true`)        | `examples/pirate.txt`, `examples/waterfall.txt`, `examples/pig.txt` |
| 3..8-gon faces (all arities)           | `examples/advanced_meshes.txt` |
| Scale-animation keyframes               | `examples/pig.txt`          |
| Multi-tile UV layout + texture painting | `examples/pirate.txt`, `examples/waterfall.txt` |
| `watermark2` / scanlines / outline settings | `examples/pig.txt`     |
| Bookmark vs. main camera divergence     | `examples/waterfall.txt`    |
| Orthographic spritesheet vs. perspective export | `examples/pirate.txt` |
| Building a model with the Python toolkit | `scripts/gen_football.py`, `scripts/gen_cube.py` |
| Toolkit-enforced invariants             | `tests/test_smoke.py`, `picocad/model.py:Model.validate` |