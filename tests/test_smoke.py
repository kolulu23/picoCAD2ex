"""Smoke tests for the picocad toolkit.

Asserts the picoCAD file-format invariants on a built model so a
regression that would produce an unloadable file is caught immediately.
Run::

    uv run pytest
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from picocad.model import Model
from scripts.gen_cube import build_cube


def _first_mesh(model: Model) -> dict[str, Any]:
    """Return the first child mesh dict from a built model's JSON."""
    graph = model.to_json()["graph"]
    assert isinstance(graph, dict)
    children = graph["children"]
    assert isinstance(children, list)
    assert children, "model root must have at least one child"
    mesh = children[0]["mesh"]
    assert isinstance(mesh, dict)
    return mesh


def test_cube_has_expected_vertex_count() -> None:
    """The unit cube has exactly 8 vertices and 6 quad faces."""
    model = build_cube()
    mesh = _first_mesh(model)
    assert len(mesh["vertices"]) == 8 * 3
    assert len(mesh["faces"]) == 6


def test_vertex_ids_are_one_based() -> None:
    """picoCAD stores vertices in a Lua table; id 0 is nil and crashes on load."""
    model = build_cube()
    mesh = _first_mesh(model)
    all_ids = [vid for face in mesh["faces"] for vid in face["vertex_ids"]]
    assert min(all_ids) >= 1, f"vertex_ids must be 1-based; got min={min(all_ids)}"
    assert max(all_ids) <= 8, f"only 8 verts exist; got max id={max(all_ids)}"


def test_face_uvs_match_vertex_count() -> None:
    """Each face needs one UV pair per vertex."""
    model = build_cube()
    mesh = _first_mesh(model)
    for face in mesh["faces"]:
        assert len(face["vertex_ids"]) * 2 == len(face["uvs"])


def test_texture_invariants() -> None:
    """Texture is exactly 128x128 pixels with 16 colors and 16-entry ramps."""
    model = build_cube()
    tex = model.to_json()["texture"]
    assert isinstance(tex, dict)
    assert len(tex["colors"]) == 16
    assert len(tex["pixels"]) == 16384
    assert len(tex["shade_pal_1"]) == 16
    assert len(tex["shade_pal_2"]) == 16


def test_metadata_version() -> None:
    """Every model file declares its format version."""
    model = build_cube()
    metadata = model.to_json()["metadata"]
    assert isinstance(metadata, dict)
    assert metadata["version"] == "2.0"


def test_every_node_has_four_motion_tracks() -> None:
    """picoCAD writes 4 tracks per node even when empty; missing them corrupts state."""
    model = build_cube()
    graph = model.to_json()["graph"]
    assert isinstance(graph, dict)
    check_motions(graph)


def check_motions(node: dict[str, Any]) -> None:
    motions = node["motions"]
    assert isinstance(motions, dict)
    tracks = motions["tracks"]
    assert isinstance(tracks, list), "tracks must be a list"
    assert len(tracks) == 4, f"every node must have 4 motion tracks, got {len(tracks)}"
    children = node["children"]
    assert isinstance(children, list)
    for child in children:
        assert isinstance(child, dict)
        check_motions(child)


def test_write_roundtrip_produces_loadable_file(tmp_path: Path) -> None:
    """Writing the model and re-parsing it yields the same invariants."""
    model = build_cube()
    out = tmp_path / "cube.txt"
    model.write(out)
    parsed = json.loads(out.read_text(encoding="ascii"))
    mesh = parsed["graph"]["children"][0]["mesh"]
    assert isinstance(mesh, dict)
    assert len(mesh["vertices"]) == 8 * 3


def test_multiple_models_share_no_state() -> None:
    """Building two cubes does not bleed state between them (sanity check)."""
    a = build_cube()
    b = build_cube()
    a_mesh = _first_mesh(a)
    b_mesh = _first_mesh(b)
    assert a_mesh["vertices"] == b_mesh["vertices"]
    assert a_mesh is not b_mesh
