# picoCAD 2 Model File Schema

A formal description of the canonical `*.txt` model file format, as inferred from the example files:

- `examples/rig.txt`        — truck/rig with nested groups, no metadata head
- `examples/pig.txt`        — animated character (scale keyframes)
- `examples/pirate.txt`     — character with many `dbl` faces and folders
- `examples/waterfall.txt`  — scene with folder groups (`landscape`, `deco`)
- `examples/livingroom.txt` — room scene, `shading_mode:0`
- `examples/advanced_meshes.txt` — polyhedra showing 3/4/5/6/8-gon faces

All example files are JSON objects with exactly three top-level keys, in any order:
`texture`, `graph`, `metadata`.

---

## 1. Top-level structure

```json
{
  "texture":  { ... },   // palette + indexed-pixel texture image
  "graph":    { ... },   // recursive scene/object tree
  "metadata": { ... }    // editor/export/camera state
}
```

All three keys are present in every current (v2.0) file. `rig.txt`'s `metadata`
appears late in the file (around line 2908) but is present — the earlier
truncation made it look optional.

---

## 2. `texture`

```json
"texture": {
  "transparent_color": <int 0..15>,        // palette index treated as fully transparent
  "background_color":  <int 0..15>,        // palette index used as the texture's base fill
  "colors":  [[r,g,b], ... 16 entries],    // the 16-color palette; r,g,b are floats in 0..1
  "shade_pal_1": [<16 ints>],              // lit-side shade remap table
  "shade_pal_2": [<16 ints>],              // shadow-side shade remap table
  "pixels": "<4096 hex chars>"             // 64x64 indexed image, row-major, one char per pixel
}
```

- `colors` always has exactly 16 RGB triples (each component is a float, 0..1). Example
  from `pig.txt`:
  ```json
  "colors":[[0,0,0],[0.11372549019608,0.16862745098039,0.32549019607843], ...]
  ```
- `shade_pal_1` / `shade_pal_2` always have 16 entries. Most entries are in `0..15`
  (a palette index to substitute). The sentinel value **`31`** also appears — it means
  "do not remap, keep the original color here". Example from `waterfall.txt`:
  ```json
  "shade_pal_1":[0,31,2,2,3,1,5,6,8,8,9,11,11,12,9,14]
  ```
- `pixels` is one contiguous hex string of length `64*64 = 4096`. Each character is a
  single hex digit `0..F` selecting a color from `colors`. Rows are laid out
  top-to-bottom, left-to-right.

---

## 3. `graph` — the scene tree

`graph` is the **root node** of a recursive tree. Every node follows the same shape;
the presence/absence of certain keys determines its kind.

### 3.1 Node shape

```json
{
  "name":      "<string>",                 // node label; root is conventionally "root"
  "visible":   <bool>,                     // editor visibility
  "open":      <bool>,                     // UI tree-expanded state
  "locked":    <bool>,                     // editor lock flag
  "transform": { ... },                    // local transform (see 3.2)
  "motions":   { "tracks": [...] },       // animation tracks (see 3.3)
  "children":  [ ...node... ],             // child nodes; empty array for leaves
  // EITHER:
  "mesh":      { ... },                    // present on geometry leaves (see 3.4)
  // OR:
  "folder":    <bool>                      // true on group/empty nodes with no mesh
}
```

Rule (confirmed across all examples):
- A node carrying `mesh` is a **geometry leaf**; it has `children:[]` and no `folder` key.
- A node carrying `"folder":true` is a **group**; it has no `mesh` and typically has
  non-empty `children`.
- The root node behaves like a group but in some files (e.g. `rig.txt`) omits both
  `name` and `folder`.

Group example from `waterfall.txt`:
```json
{
  "name":"landscape",
  "folder":true,
  "visible":true,"open":false,"locked":true,
  "transform":{ "pos":{"x":0,"y":0,"z":0},
                 "scale":{"x":1,"y":1,"z":1},
                 "rot":{"x":0,"y":0,"z":0} },
  "motions":{ "tracks":[[],[],[],[]] },
  "children":[ ... ]
}
```

### 3.2 `transform`

```json
"transform": {
  "pos":   {"x":<n>, "y":<n>, "z":<n>},    // local translation
  "scale": {"x":<n>, "y":<n>, "z":<n>},    // local scale (1,1,1 = identity)
  "rot":   {"x":<n>, "y":<n>, "z":<n>}      // local rotation (radians)
}
```
All three sub-objects are always present, each with `x`,`y`,`z` numeric fields
(key order in objects is not significant). Identity defaults: `pos=(0,0,0)`,
`scale=(1,1,1)`, `rot=(0,0,0)`.

### 3.3 `motions`

```json
"motions": {
  "tracks": [ [], [], [], [] ]    // always a 4-element array
}
```

- `tracks` is always a 4-element array (one per animation channel/slot). An empty
  track is just `[]`. A non-empty track is a list of keyframe objects.

Keyframe shape (only `"scale"` is observed in the examples; `pos`/`rot` are
plausible but **unverified**):

```json
{
  "prop":   "scale",                  // animated property (known: "scale")
  "axises": ["x"|"y"|"z", ...],      // axes affected (may list multiple)
  "start":  <num>,                     // start frame
  "stop":   <num>,                     // end frame
  "times":  <int>,                     // number of cycles/repeats
  "delta":  <num>,                     // per-cycle change applied to the axes
  "icon":   <int>                      // UI icon id (e.g. 470)
}
```

Example from `pig.txt`:
```json
"motions":{ "tracks":[
  [{ "prop":"scale","times":3,"stop":4,"icon":470,"delta":0.1, "start":0,"axises":["y"] }],
  [{ "prop":"scale","times":3,"stop":4,"icon":470,"delta":-0.05,"start":0,"axises":["z"] }],
  [{ "prop":"scale","times":3,"stop":4,"icon":470,"delta":-0.05,"start":0,"axises":["x"] }],
  []
]}
```

### 3.4 `mesh` (geometry leaves)

```json
"mesh": {
  "name":     "<string>",                 // mesh name (usually matches the node name)
  "vertices": [x,y,z, x,y,z, ...],       // flat list of floats, 3 per vertex
  "faces":    [ ...face... ]              // list of polygonal faces
}
```

- `vertices` is a flat numeric array of length `3 * N`. Vertex **k** (1-based) occupies
  indices `[3(k-1), 3(k-1)+1, 3(k-1)+2]`.
- Coordinates are arbitrary floats; small values like `5.5511151231258e-17`
  appear (mathematical-zero residue) and are fine.

### 3.5 Face shape

```json
{
  "color":      <int 0..15>,                  // palette index for this face
  "vertex_ids": [<int>, ...],                 // 1-based indices into vertices[]; 3..8 corners
  "uvs":        [<u0>,<v0>,<u1>,<v1>, ...],   // UV per corner, length = 2*len(vertex_ids)
  "notex":       <bool>,                       // optional; true = solid color, ignore UVs
  "dbl":         <bool>                        // optional; true = render double-sided
}
```

- `vertex_ids` length determines face arity. **All of 3, 4, 5, 6, and 8 are
  confirmed** by `advanced_meshes.txt` (triangles, quads, dodecahedron pentagons,
  hex_antiprism hexagons, oct_antiprism octagons). 7-gons are not attested but
  the format does not forbid them; accept 3..8.
- `uvs` is a parallel flat list of 2*corners floats, packed in corner order:
  `[u0,v0, u1,v1, ...]`. UVs are in `0..1` (clamped/repeated by the texture).
- `notex` is **optional**. Omitting it is equivalent to `false` (use the texture).
  When `notex:true`, the face is filled with the solid palette color and the `uvs`
  value is ignored (commonly a boilerplate `[0.375,0,0.5,0,...]`). Example with
  both flags from `pirate.txt`:
  ```json
  { "dbl":true,"color":13,"uvs":[...4 corners...],"vertex_ids":[6,5,8,7] }
  ```
  Example `notex` face from `rig.txt`:
  ```json
  { "notex":true,"color":3,"uvs":[0.625,0.3125,...],"vertex_ids":[6,5,8,7] }
  ```
- `dbl` is **optional**; defaults to `false`. Confirmed across `pig`, `pirate`,
  `waterfall` (fences).

---

## 4. `metadata`

Always present in v2.0 files.

```json
"metadata": {
  "version": "2.0",                       // always "2.0" in the examples

  "camera": {
    "distance_to_target": <num>,
    "omega": <num>,                       // azimuth angle (radians or radians-ish)
    "theta": <num>,                       // elevation angle
    "pos":    {"x","y","z"},              // camera position
    "target": {"x","y","z"},              // orbit pivot
    "bookmark": {                         // optional saved camera view
      "distance_to_target": <num>,        //   (any subset of the above fields)
      "omega": <num>, "theta": <num>,
      "pos": {...}, "target": {...}
    }
  },

  "shading_mode": <int 0|1>,              // editor shading mode (observed: 0 and 1)
  "face_mode":    <int>,                  // editor face display mode (only 2 observed)
  "motion_duration": <int>,              // length of the animation timeline (frames)

  "spritesheet_settings": {
    "frame_width":  <int>,                // output frame size in px (e.g. 48, 64)
    "num_frames":   <int>,                // total frames in the spritesheet
    "cam_dist":     <num>,                // spritesheet camera distance
    "cam_theta":    <num>,                // spritesheet camera elevation
    "cam_target_y": <num>,                // spritesheet target Y offset
    "cam_ortho":    <bool>                // true = orthographic camera for the sheet
  },

  "export_settings": {
    "animate":          <bool>,           // OPTIONAL; whether to render an animation
    "anim":             "spin" | "sway",  // animation type (only these two observed)
    "speed":            <num>,            // animation playback speed
    "size":             <int>,            // output image resolution (e.g. 128)
    "scale":            <num>,            // output pixel scale (e.g. 3)
    "fov_type":         "perspective",   // projection (only "perspective" observed)
    "dir":              <int>,            // spin direction (e.g. -1)
    "scanlines":        <bool>,           // enable scanline shader
    "scanline_color":   <int 0..15>,      // scanline palette index
    "outline_size":     <int>,            // outline thickness in px (0 = none)
    "outline_color":    <int 0..15>,      // outline palette index
    "watermark":        "<string>",       // primary watermark text (e.g. "#picoCAD2")
    "watermark_color":  <int 0..15>,      // primary watermark palette index
    "watermark2":       "<string>",       // secondary watermark text (often "")
    "watermark2_color": <int 0..15>       // secondary watermark palette index
  }
}
```

Notes from cross-checking the examples:
- `export_settings.animate` is **optional**: present in `pig`/`pirate`, absent in
  `waterfall`/`livingroom`/`advanced_meshes`. Treat missing as `false`.
- `export_settings.anim` observed values are exactly `"spin"` and `"sway"`. No
  `"idle"` or other values appear in any example.
- `export_settings.fov_type` is always `"perspective"` even when
  `spritesheet_settings.cam_ortho` is `true`. The two cameras are separate.
- `shading_mode` observed values: `0` (livingroom) and `1` (others).
- `face_mode` is `2` in every example; the enum is not otherwise attested.
- `camera.bookmark` may omit fields (`waterfall`'s bookmark omits
  `distance_to_target` and `pos`); it stores whatever the user saved.
- `camera.omega` is a free float — `rig.txt` uses `-13.125`, `pirate.txt` `0.3`.

Example from `pirate.txt`:
```json
"metadata":{
  "version":"2.0",
  "face_mode":2,
  "camera":{ "distance_to_target":20.595667879956,
              "pos":{...}, "target":{...},
              "bookmark":{ "theta":0.1, "omega":0.3, ... },
              "theta":0.1, "omega":0.3 },
  "spritesheet_settings":{ "frame_width":64, "num_frames":56,
                           "cam_dist":29, "cam_target_y":5.5,
                           "cam_theta":0.3, "cam_ortho":true },
  "motion_duration":8,
  "export_settings":{ "anim":"sway", "speed":8, "size":128, "scale":3,
                       "fov_type":"perspective", "scanlines":false,
                       "outline_size":0, "outline_color":4,
                       "watermark":"#picoCAD2","watermark_color":15,
                       "watermark2":"","watermark2_color":15,
                       "dir":-1, "animate":true },
  "shading_mode":1
}
```

---

## 5. Invariants & cardinalities (quick reference)

| Field                              | Required | Type / range                          | Notes |
|------------------------------------|----------|----------------------------------------|-------|
| `texture.colors`                   | yes      | array of exactly 16 [r,g,b]            | floats 0..1 |
| `texture.shade_pal_1/2`            | yes      | array of exactly 16 ints               | values 0..15, or 31 (no-remap) |
| `texture.pixels`                   | yes      | string of exactly 4096 hex chars       | 64x64 indexed image |
| `texture.transparent_color`        | yes      | int 0..15                              | |
| `texture.background_color`         | yes      | int 0..15                              | |
| `graph.name`                       | usually  | string                                 | root may omit |
| `graph.transform.{pos,scale,rot}`  | yes      | {x,y,z} of numbers                     | |
| `graph.motions.tracks`             | yes      | 4-element array of keyframe-arrays      | can be all `[]` |
| `graph.children`                   | yes      | array of nodes                         | `[]` for leaves |
| `graph.mesh` OR `graph.folder`     | one      | mesh-object / `true`                   | mutually exclusive |
| `mesh.vertices`                    | yes      | flat array, length = 3 * vertex_count   | floats |
| `mesh.faces[]`                     | yes      | array of face-objects                   | may be empty |
| face.`vertex_ids`                  | yes      | array of 3..8 ints, 1-based             | |
| face.`uvs`                         | yes      | array of 2*corners floats               | ignored if `notex:true` |
| face.`color`                       | yes      | int 0..15                              | |
| face.`notex`                       | no       | bool                                   | default false |
| face.`dbl`                         | no       | bool                                   | default false |
| keyframe.`prop`                    | yes      | `"scale"` (only attested)              | `pos`/`rot` unverified |
| keyframe.`axises`                  | yes      | array of `"x"`/`"y"`/`"z"`             | may contain multiple |
| keyframe.`start`,`stop`,`times`,`delta`,`icon` | yes | number/int          | |
| `metadata.version`                 | yes      | `"2.0"`                                | |
| `metadata.shading_mode`            | yes      | int (0 or 1 observed)                  | |
| `metadata.face_mode`               | yes      | int (only 2 observed)                  | |
| `metadata.motion_duration`         | yes      | int                                    | |
| `metadata.camera`                  | yes      | object                                 | bookmark optional |
| `metadata.spritesheet_settings`    | yes      | object                                 | |
| `metadata.export_settings`         | yes      | object                                 | `animate` optional within |

---

## 6. Limitations / open questions

- `keyframe.prop`: only `"scale"` is attested. The same keyframe structure likely
  supports `"pos"` and `"rot"` (the editor exposes those animations), but no example
  exercises it. Treat as "known: scale; others unverified".
- `face_mode` enum values other than `2`: unknown.
- `export_settings.anim` other than `spin`/`sway`: not attested.
- 7-gon faces: no example contains exactly 7 corners, but the parser clearly
  accepts variable arity (3..8); 7 is plausibly valid.
- `shade_pal_* = 31` semantics ("no remap") is inferred from usage; the editor
  source is not available.
- JSON object key order is not semantic; arrays are ordered (vertices, faces,
  tracks, children, uvs, vertex_ids).