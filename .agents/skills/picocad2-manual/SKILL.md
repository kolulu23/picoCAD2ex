---
name: picocad2-manual
description: >-
  Reference for the picoCAD 2 low‑poly 3D modeling tool. Use when the user
  edits, generates, inspects, or asks about picoCAD 2 model files
  (`*.txt` JSON files under `picocad2`/`%AppData%/Roaming/picoCAD2`), their
  texture/animation/export formats, or wants to author meshes, UVs, palettes,
  shading ramps, animation clips, or export settings by hand. Also use to
  answer questions about picoCAD's intentional limitations vs full 3D DCCs
  such as Blender.
---

# picoCAD 2 — Operator's Reference

This skill is distilled from the official manual at
<https://picocad.net/manual/> (last verified 2026-03-29) and cross-checked
against real model files in `%AppData%\Roaming\picoCAD2\`. **picoCAD 2 is
deliberately limited** — do not invent features the manual does not list.
Blender-style operations (booleans, subdivision, bevels, skeletons, materials,
particles, etc.) do **not** exist; politely suggest the closest supported
workflow instead.

Authoritative source of truth for any missing detail: the manual URL above, or
running picoCAD 2 itself.

## Filesystem layout

Operating system data folders (per the manual's Troubleshooting section):

- Windows: `%AppData%\Roaming\picoCAD2\`
- macOS:   `~/Library/Application Support/picoCAD2/`

The cwd for this project *is* the Windows data folder. Typical contents:

- `<modelName>.txt`        — model files (JSON, see "File format" below).
- `backups/`               — auto backups named `YYYYMMDD_HHMMSS_<model>.txt`.
- `examples/`              — sample models (pig, rig, pirate, livingroom,
                             waterfall, advanced_meshes) and an OBJ/GLTF/PNG
                             export sample (`pirate.obj`/`gltf`/`png`).
- `.picocad/`              — `default_texture.png`, `ignore.txt`.
- `settings.json`         — user settings (see "Settings").
- `gifcatlib.dll`          — GIF library (do not modify).

When proposing new files, write `.txt` files written from the JSON format below
into this folder so picoCAD lists them under "Open". Avoid non-ASCII characters
in **both file and folder paths** — picoCAD silently fails exports when the
account/install path contains them (manual, Troubleshooting).

## The three modes

1. **Modeling** — add primitives, edit vertices, UV-unmapped meshes.
2. **Texturing** — UV edit `/` pixel paint, palette + shading ramps.
3. **Animating** — per-mesh clip timeline, up to 4 tracks per mesh.

Switch between them in-app; they are not separate files.

## Modeling

Four viewports (top/front/side/3D). 3D is top-right. `SPACE` toggles the
active viewport fullscreen. Cameras: mouse drag, wheel zoom; arrow keys pan.

### Adding primitives

`[+]` toolbar button, or right-click in empty viewport and pick a primitive.
Right-click placement: the new primitive faces the camera of the viewport it
was added in.

### Vertex operations

| Action                  | How                                                            |
| ----------------------- | -------------------------------------------------------------- |
| Select vertex           | Left-click. Multi: `SHIFT`+click, or drag rectangle. In 3D viewport hold `CTRL` before dragging to rectangle-select (otherwise it selects only the top-most). |
| Move                    | Drag with LMB, arrow keys, or `WASD`.                          |
| Nudge (snap-step)       | `CTRL` + arrow keys / `WASD`.                                  |
| Merge                   | Right-click selected verts → "merge".                         |
| Snap to world grid      | Right-click selected verts → "snap to grid".                  |
| Delete                  | Right-click verts → "delete", or `DEL`/`BACKSPACE`.           |
| Toggle snap while drag  | Hold `CTRL` while dragging.                                    |

### Mesh operations

| Action                  | How                                                            |
| ----------------------- | -------------------------------------------------------------- |
| Move mesh               | LMB + drag.                                                    |
| Move mesh **center point** (used for rotate/scale/animation pivot) | LMB-drag, then hold `SHIFT`.        |
| Rotate mesh             | Hold `R`, then LMB + drag.                                     |
| Scale mesh              | Hold `T`, then LMB + drag.                                     |
| Toggle snap             | Hold `CTRL` while dragging.                                    |

### Per-face / per-mesh properties (right-click menu on a face)

Per face: `color`, `double sided` (`dbl`), `shaded`, `textured`, `draw behind`.
Per mesh operations: `Extrude face`, `Delete face`, `Mirror mesh`, `Clone
mesh`, `Delete mesh`. Traditional `CTRL+C/V/X` copy/paste/cut work on meshes.

### Project overview (press `O`)

Lock, hide, organize into folders, rename (double-click), merge folder into
single mesh (right-click), duplicate (right-click).

### Keyboard shortcuts

`E` extrude face (hover) · `X` delete face (hover) · `CTRL+X` delete mesh (hover) ·
`CTRL+C/V` copy/paste mesh (hover) · `DEL`/`BACKSPACE` delete vertices ·
`F` face properties (hover) · `G` mesh properties (hover) · `O` project overview ·
hold `CTRL` when dragging = toggle snap · `SPACE` fullscreen viewport ·
`CTRL+Z/Y` undo/redo · `M` cycle render mode · `L` toggle shading ·
`R` then drag = rotate mesh · `T` then drag = scale mesh.

## Texturing

Hard limits: **128×128 px**, **16 colors** (one of which maps to transparent).
PNG import via menu or drag-and-drop; >16 colors → best-effort color reduction.

### UV mapping

Select face(s) (SHIFT for multi) → their UVs highlight on the texture. Drag
UVs with the **UV tool selected** (shortcut `V`). Right-click UV → "rotate" or
"flip"; or hover face/UV and press `R` rotate, `H` flip. `T` then drag scales
UVs. Copy/paste UV map: `CTRL+C/V` while hovering a face.

### Pixel painting tools

| Icon                 | Tool     | Shortcut | Notes                                                           |
| -------------------- | -------- | -------- | --------------------------------------------------------------- |
| pointer              | UV tool  | `V`      | Required for editing UVs.                                       |
| pen                  | Pen      | `B`      | Freehand. `SHIFT` = locked axis + straight line between clicks.  |
| (eyedropper)         | Eye drop | `I`      | Set active color.                                              |
| (fill)               | Fill     | `G`      | Flood fill.                                                    |
| (line)               | Line     | —        | Two-point line.                                                |
| (rectangle)          | Recangle | —        | Click again to toggle filled.                                  |
| (circle)             | Circle   | —        | Click again to toggle filled.                                  |
| (marquee)            | Marquee  | —        | Move/copy the marked region.                                   |

Zoom: `1` `2` `3` `4` presets, mouse wheel. Pan: `SPACE`+drag or middle-mouse
drag. Grid button bottom-left. Palette: `P`. Pick color: hold `CTRL` and click.
If "secondary colors" is enabled in settings: LMB=`fg` palette color,
RMB=`bg` palette color. Paste colors with normal `CTRL+V`.

### Palette and shading (the picoCAD aesthetic)

Palette panel has two halves:

- **Top:** select/edit colors, set `bg` (background, drawn behind everything)
  and `alpha` (transparent). Click palette icon buttons:
  - swap two colors (`SHIFT`+click for the second).
  - ramp between two colors (`SHIFT`+click).
  - choose from predefined palettes.
  - auto-shade (the robot button — best effort ramps).
- **Bottom:** shading ramps. Drag a color into a ramp slot to control what
  color this one becomes when shaded. Hover the ramp slot to preview on the
  cube below. If the palette gets messy, the reset button restores defaults.

## Animating

One timeline shared across the model. **Each mesh has up to 4 tracks.** Each
track can hold multiple clips. Clips animate the mesh's own transform relative
to its modeled transform; settings on the mesh's `transform.{pos,rot,scale}` are
the rest pose.

**Pivot:** rotating/scaling clips use the mesh's **center point**. The pivot
drifts during modeling, so re-adjust it (in Modeling mode, drag the mesh then
hold `SHIFT`) before animating.

### Clip types

| Clip        | Affects   | Notes                                              |
| ----------- | --------- | -------------------------------------------------- |
| Movement    | position  | Move along chosen axis. Color-coded.               |
| Rotation    | rotation  | Rotate around chosen axis, about the center point. |
| Scale       | scale     | Scale along chosen axis.                           |
| Visibility  | hide      | Hide the mesh entirely for the clip's duration.    |
| Oscilation  | any prop  | Sine-wave wobble: amplitude handled like Movement/Rotation/Scale; adds a **Frequency** property. |

Color/icon indicates which property. Drag a clip onto the timeline from the
clip library; drag the body to move, drag side handles to resize duration.

### Clip properties (right panel)

- **Distance / Rotation / Scale** — `delta` magnitude.
- **Curve** — easing curve to apply.
- **Ping pong** — return to start at the end.
- **Frequency** (oscillation only) — sine frequency.
- **Axes (axises)** — which of `x`/`y`/`z` to affect.

`CTRL+C/V` duplicates clips across meshes. Double-click the timer at the end of
the timeline to change the timeline length. Hold `CTRL` while dragging clips
to disable snapping. `SPACE` or the play button previews; mouse-scrub to jog.

## Exporting

| Format     | When to use | Output                                            |
| ---------- | ----------- | ------------------------------------------------- |
| GIF        | Social share| `<name>.gif` in cwd (auto-opens output folder).   |
| Sprite sheet | 2D games | `<name>_NNN.png` rotated frames (auto-opens folder). |
| GLTF       | Game engines| `.gltf` + `.bin` + `.png`.                        |
| OBJ/MTL    | Wide compatibility | `.obj` + `.mtl` + `.png`.                  |
| Texture only| Pixel art | `.png`.                                          |

### GIF export controls

**Camera panel:** Camera animation/direction (e.g. `spin`). **Animate** → play
the animation (overrides **Duration** and uses `motion_duration`). **Duration**
sets length when no animation is used. **Effects:** Outline (size+color),
Scanlines color, FOV (lens distortion). **Text:** left tag + color, right tag +
color. **Dimensions:** base size + scale factor. Settings persist into
`metadata.export_settings` per model.

### Sprite sheet export controls

`Distance` (cam distance) · `Tilt` (cam angle) · `Height` (look target Y) ·
`Ortho` (orthographic projection) · `Frames` (count) · `Size(px)` (per-frame
W×H). Live preview. Persist into `metadata.spritesheet_settings`.

If exports don't appear on disk, the path contains non-ASCII characters in the
install/account name — install/reinstall picoCAD with an ASCII-only user
account.

## Settings (`settings.json`)

| Key                    | Effect                                                                 |
| ---------------------- | ---------------------------------------------------------------------- |
| `snap_is_default`        | Snap-on default; toggle anytime by holding `CTRL`.                  |
| `texture_grid_size`      | Help-grid cell size on the texture (default ~8).                    |
| `rmb_action`             | RMB in texture mode: `0` pan, `1` secondary color, `2` pick color.  |
| `auto_save_frequency`     | Backup interval in minutes (0 disables). Use the folder icon to jump to backups. |
| `gif_file_increment`     | If true, exported GIFs auto-suffix `_NN` on clash instead of overwriting. |
| `os_mouse`               | Use the OS cursor vs picoCAD's pixel cursor.                         |
| `invert_zoom`            | Invert wheel zoom.                                                    |
| `invert_mouse_controls`  | Invert other mouse controls.                                         |
| `theme`                  | UI theme (`classic`, …).                                              |
| `show_grid`              | Show texture grid on by default.                                      |
| `warn_on_exit`           | Warn before quitting.                                                 |
| `window_width/height`    | Last window size.                                                     |
| `last_path`/`recent_files`| File picker state.                                                   |

Reset settings: hold `R` during boot.

## File format (`*.txt`)

A model is **JSON** with three top-level keys: `metadata`, `texture`, `graph`.
Whitespace-insensitive; the `pixels` string is always 16384 hex chars (128×128).

### `metadata`

```jsonc
{
  "version": "2.0",
  "motion_duration": 4,            // timeline length in seconds
  "shading_mode": 1,              // 0/1 = shading mode (cycled by L)
  "face_mode": 2,                  // viewport render mode (cycled by M)
  "camera": { "pos":{x,y,z}, "target":{x,y,z},
              "distance_to_target": 6.3, "omega": 0.3, "theta": 0.5,
              "bookmark": { ... same shape ... } }, // 3D viewport bookmark
  "export_settings":   { ... },   // last-used GIF export settings
  "spritesheet_settings": { ... } // last-used sprite sheet settings
}
```

### `texture`

```jsonc
{
  "colors":  [ [r,g,b], ... ] x16,   // 0..1 floats
  "pixels":  "ccccccccc...",          // 16384 hex chars, 16 = 128*128 indices
  "shade_pal_1": [0,0,1,1,2,3,3,2,6,7,4,5,6,10,10,12], // lit-row ramp
  "shade_pal_2": [0,0,0,0,1,1,1,1,3,2,2,3,3,4,4,6],    // shaded-row ramp
  "transparent_color": 0,  // palette index treated as transparent
  "background_color": 1    // palette index drawn as background (the `bg` color)
}
```

Reading `pixels`: row-major top-to-bottom, each hex digit is a palette index
into `colors`. Index > 9 = `a..f`. UTC-space UV `[0,1]` corresponds to the
full 128×128 image with origin in the same corner as displayed.

### `graph` (scene tree)

Lines list of nodes. The root node is `name:"root"`. Recursive shape:

```jsonc
{
  "name":     "root" | "cylinder" | "somefolder",
  "open":     false,        // expanded in project overview
  "locked":   false,        // editing locked
  "visible":  true,
  "transform": { "pos":{x,y,z}, "rot":{x,y,z}, "scale":{x,y,z} }, // rest pose
  "motions":  { "tracks": [ [], [], [], [] ] },                   // 4 tracks
  "mesh":     null | { ...mesh... },                              // folders have no mesh
  "children":  [ ...recurse... ]
}
```

Folder/leaf order in `children` = display order in the Project Overview
(`O`). To turn a folder into one merged mesh: use the right-click "merge"
action in-app (the file format still writes one mesh per node; merging is a
UI/numeric op).

### `mesh`

```jsonc
{
  "name": "cylinder",     // primitive name
  "vertices": [ v0x,v0y,v0z, v1x,v1y,v1z, ... ],   // flat xyz; **1-BASED** in Lua (id 1..N)
  "faces": [
    {
      "vertex_ids": [8,7,6,5,4,3,2,1],              // **1-BASED** ids (1..len(vertices)) — id 0 → nil crash
      "uvs":        [ u0,v0, u1,v1, ... ],          // one uv pair per vertex
      "color":      10,                              // 0..15 palette index, used when not textured
      "dbl":        false                            // optional: double-sided?
    }
  ]
}
```

Optional/observed per-face flags (mostly omitted unless toggled): `dbl`,
`shaded`, `textured`, `drawBehind`. UV pairs are flat floats in [0,1].

### Animation clip object (inside a track)

```jsonc
{
  "prop":   "scale" | "position" | "rotation" | "visibility" | "oscillation",
  "icon":   470,                 // icon index (color-coded)
  "start":  0,                   // timeline start time, seconds
  "stop":   4,                   // timeline stop time, seconds
  "times":  3,                   // duration multiplier / repeat count
  "delta":  0.1,                 // amount to change the property
  "axises": ["y"],               // subset of ["x","y","z"]
  "curve":  "...",               // easing curve (manual key)
  "ping":   false,               // true = ping-pong
  "freq":   1.0                  // oscillation sine frequency (oscilation only)
}
```

> Verified fields actually written by picoCAD: `prop`, `icon`, `start`,
> `stop`, `times`, `delta`, `axises`. `curve`, `ping`, `freq` exist per the
> manual's property panel description; if you author by hand and picoCAD
> doesn't read them, leave at default.

## Worked authoring patterns (within picoCAD's intentional limits)

- **Symmetry:** model and UV one half, then `Clone mesh` / `Mirror mesh` /
  duplicate-and-flip via right-click, or copy/paste UV map (`CTRL+C`/`V`) so the
  same texture serves both halves. Also saves UV space.
- **Texture space:** `128×128` fills up fast; reuse UV areas across faces
  (multiple faces can point to identical UV rectangles). Roughly keep face
  scale and texture region scale matching.
- **Affine warping:** texture warps in strong perspective because picoCAD uses
  PS1-style affine mapping. Subdivide big faces rather than tweaking UVs.
- **Pivot for rotation clips:** drag mesh then `SHIFT` to park the center
  point before animating.
- **Cross-instance paste:** multiple picoCAD windows can be open at once
  (open via File Explorer if Steam blocks second launch); copy meshes/UVs
  between them.
- **Reference camera:** `SHIFT`+click the bookmark button in the 3D viewport
  to reset the camera when it won't center.

## Backups

`backups/YYYYMMDD_HHMMSS_<modelname>.txt`. Restoring: copy to the project root,
rename to `<modelname>.txt`. The `.picocad/ignore.txt` is reserved; the
`default_texture.png` is the new-file template texture.

## Quick do/don't for LLM authors

DO:
- Treat the file as JSON; pretty or minified, both load.
- Keep `vertices` arrays as offsets *only when* the mesh node is a primitive;
  for edited meshes the values are world-or-local-relative per the parent's
  `transform`.
- Index into `colors` with `0..15`; only those 16 colors exist.
- Use `vertex_ids` and `uvs` aligned 1:1 per face; winding defines the forward
  direction.

DON'T:
- Add subdivision/booleans/bevels/armatures/shaders/materials/particles — none
  exist; suggest extrude + primitive blocking instead.
- Exceed 16 colors in `colors`, or write `pixels` longer/shorter than 16384
  chars.
- Write non-ASCII characters in `metadata.watermark`, file names, or directory
  paths (breaks GIF export).
- Invent clip `prop` values other than those listed above.
- Set `transform.scale` to 0 on any axis (degenerates the mesh).
- Expect CSG, vertex normals edits, named materials, or image referencing —
  not in picoCAD 2.