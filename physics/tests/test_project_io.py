"""
Tests for physics.project_io — HDF5 round-trip save/load and validate_import.

Covers:
  - Round-trip fidelity for all geometry types
  - Optional field preservation (colour, notes, groupId, creatorMetadata, locked)
  - Multiple coils and groups
  - Overwrite behaviour
  - Load error paths (missing file, corrupt HDF5, bad JSON, bad Pydantic)
  - validate_import version compatibility rules
"""

from __future__ import annotations

import json
from pathlib import Path

import h5py
import pytest
from pydantic import ValidationError

from physics.project_io import ValidationResult, load_project, save_project, validate_import
from physics.types import (
    CircularGeometry,
    CoilDef,
    EllipticalGeometry,
    ElongatedToroidalGeometry,
    GroupDef,
    ProjectFile,
    RacetrackGeometry,
    ToroidalGeometry,
    Vec3,
    WindingSpec,
    WireSpec,
)
from physics.version import SCHEMA_VERSION


# ---------------------------------------------------------------------------
# Shared helpers / factories
# ---------------------------------------------------------------------------

_WIRE = WireSpec(
    awg=24,
    label="AWG24",
    bareD=0.000511,
    insulatedD=0.000573,
    area=2.047e-7,
)

_WINDING_FLAT = WindingSpec(
    turns=10,
    current=5.0,
    wire=_WIRE,
    channelWidth=0.006,
    windingMode=None,
)

_WINDING_TOROIDAL_POLOIDAL = WindingSpec(
    turns=20,
    current=3.0,
    wire=_WIRE,
    channelWidth=0.005,
    windingMode="poloidal",
)

_WINDING_TOROIDAL_TOROIDAL = WindingSpec(
    turns=20,
    current=3.0,
    wire=_WIRE,
    channelWidth=0.005,
    windingMode="toroidal",
)


def _center() -> Vec3:
    return Vec3(x=0.1, y=0.2, z=0.3)


def _rotation() -> Vec3:
    return Vec3(x=10.0, y=20.0, z=30.0)


def _coil(coil_id: str, geometry, winding: WindingSpec | None = None) -> CoilDef:
    return CoilDef(
        id=coil_id,
        name=f"Coil {coil_id}",
        center=_center(),
        rotationEulerDeg=_rotation(),
        geometry=geometry,
        winding=winding or _WINDING_FLAT,
    )


def _project(*coils: CoilDef, groups: list[GroupDef] | None = None, **kwargs) -> ProjectFile:
    defaults = dict(
        schemaVersion=SCHEMA_VERSION,
        appVersion="0.1.0",
        exportTimestamp="2026-03-12T00:00:00Z",
        projectName="Test Project",
        displayUnits="m",
        coils=list(coils),
        groups=groups or [],
    )
    defaults.update(kwargs)
    return ProjectFile(**defaults)


# ---------------------------------------------------------------------------
# Round-trip: all geometry types
# ---------------------------------------------------------------------------


def test_round_trip_circular(tmp_path: Path) -> None:
    geom = CircularGeometry(type="circular", radius=0.05)
    proj = _project(_coil("c1", geom))
    fpath = tmp_path / "proj.h5"

    save_project(proj, fpath)
    loaded = load_project(fpath)

    assert loaded == proj


def test_round_trip_racetrack(tmp_path: Path) -> None:
    geom = RacetrackGeometry(type="racetrack", straightLength=0.1, arcRadius=0.03)
    proj = _project(_coil("c1", geom))
    fpath = tmp_path / "proj.h5"

    save_project(proj, fpath)
    loaded = load_project(fpath)

    assert loaded == proj


def test_round_trip_elliptical(tmp_path: Path) -> None:
    geom = EllipticalGeometry(type="elliptical", semiMajor=0.08, semiMinor=0.04)
    proj = _project(_coil("c1", geom))
    fpath = tmp_path / "proj.h5"

    save_project(proj, fpath)
    loaded = load_project(fpath)

    assert loaded == proj


def test_round_trip_toroidal_poloidal(tmp_path: Path) -> None:
    geom = ToroidalGeometry(type="toroidal", majorRadius=0.1, minorRadius=0.02)
    proj = _project(_coil("c1", geom, _WINDING_TOROIDAL_POLOIDAL))
    fpath = tmp_path / "proj.h5"

    save_project(proj, fpath)
    loaded = load_project(fpath)

    assert loaded == proj


def test_round_trip_toroidal_toroidal(tmp_path: Path) -> None:
    geom = ToroidalGeometry(type="toroidal", majorRadius=0.1, minorRadius=0.02)
    proj = _project(_coil("c1", geom, _WINDING_TOROIDAL_TOROIDAL))
    fpath = tmp_path / "proj.h5"

    save_project(proj, fpath)
    loaded = load_project(fpath)

    assert loaded == proj


def test_round_trip_elongated_toroidal(tmp_path: Path) -> None:
    geom = ElongatedToroidalGeometry(
        type="elongated_toroidal", majorRadius=0.1, minorRadius=0.02, extension=0.05
    )
    proj = _project(_coil("c1", geom, _WINDING_TOROIDAL_POLOIDAL))
    fpath = tmp_path / "proj.h5"

    save_project(proj, fpath)
    loaded = load_project(fpath)

    assert loaded == proj


# ---------------------------------------------------------------------------
# Round-trip: data completeness / optional fields
# ---------------------------------------------------------------------------


def test_round_trip_optional_fields(tmp_path: Path) -> None:
    geom = CircularGeometry(type="circular", radius=0.05)
    coil = CoilDef(
        id="c-opt",
        groupId="g1",
        name="Colourful Coil",
        colour="#FF6600",
        notes="Some notes here.",
        locked=True,
        center=Vec3(x=-0.5, y=1.0, z=2.5),
        rotationEulerDeg=Vec3(x=45.0, y=0.0, z=90.0),
        geometry=geom,
        winding=_WINDING_FLAT,
    )
    proj = _project(
        coil,
        creatorMetadata={"author": "Test Suite", "institution": "Lab"},
    )
    fpath = tmp_path / "proj.h5"

    save_project(proj, fpath)
    loaded = load_project(fpath)

    assert loaded == proj
    assert loaded.coils[0].colour == "#FF6600"
    assert loaded.coils[0].notes == "Some notes here."
    assert loaded.coils[0].locked is True
    assert loaded.coils[0].groupId == "g1"
    assert loaded.creatorMetadata == {"author": "Test Suite", "institution": "Lab"}


def test_round_trip_with_groups(tmp_path: Path) -> None:
    geom = CircularGeometry(type="circular", radius=0.05)
    c1 = _coil("coil-a", geom)
    c2 = _coil("coil-b", geom)
    group = GroupDef(id="grp-1", name="Helmholtz Pair", coilIds=["coil-a", "coil-b"])
    proj = _project(c1, c2, groups=[group])
    fpath = tmp_path / "proj.h5"

    save_project(proj, fpath)
    loaded = load_project(fpath)

    assert loaded == proj
    assert len(loaded.groups) == 1
    assert loaded.groups[0].coilIds == ["coil-a", "coil-b"]


def test_round_trip_multiple_coils(tmp_path: Path) -> None:
    c1 = _coil("c1", CircularGeometry(type="circular", radius=0.05))
    c2 = _coil("c2", RacetrackGeometry(type="racetrack", straightLength=0.1, arcRadius=0.03))
    c3 = _coil(
        "c3",
        ToroidalGeometry(type="toroidal", majorRadius=0.1, minorRadius=0.02),
        _WINDING_TOROIDAL_TOROIDAL,
    )
    proj = _project(c1, c2, c3)
    fpath = tmp_path / "proj.h5"

    save_project(proj, fpath)
    loaded = load_project(fpath)

    assert loaded == proj
    assert len(loaded.coils) == 3


def test_round_trip_overwrite(tmp_path: Path) -> None:
    """Saving twice to the same path: load should return the second version."""
    fpath = tmp_path / "proj.h5"
    geom = CircularGeometry(type="circular", radius=0.05)

    proj_v1 = _project(_coil("c1", geom), projectName="Version One")
    save_project(proj_v1, fpath)

    proj_v2 = _project(_coil("c2", geom), projectName="Version Two")
    save_project(proj_v2, fpath)

    loaded = load_project(fpath)
    assert loaded.projectName == "Version Two"
    assert loaded.coils[0].id == "c2"


def test_round_trip_float_precision(tmp_path: Path) -> None:
    """High-precision floats must survive serialisation without rounding."""
    precise_x = 0.12345678901234567
    geom = CircularGeometry(type="circular", radius=0.05)
    coil = CoilDef(
        id="c1",
        name="Precision Coil",
        center=Vec3(x=precise_x, y=0.0, z=0.0),
        rotationEulerDeg=Vec3(x=0.0, y=0.0, z=0.0),
        geometry=geom,
        winding=_WINDING_FLAT,
    )
    proj = _project(coil)
    fpath = tmp_path / "proj.h5"

    save_project(proj, fpath)
    loaded = load_project(fpath)

    # Pydantic JSON round-trip is accurate to at least 15 significant figures
    assert abs(loaded.coils[0].center.x - precise_x) < 1e-15


def test_round_trip_negative_current(tmp_path: Path) -> None:
    """Signed current (negative) must be preserved exactly."""
    winding = WindingSpec(
        turns=5, current=-10.0, wire=_WIRE, channelWidth=0.004, windingMode=None
    )
    geom = CircularGeometry(type="circular", radius=0.05)
    proj = _project(_coil("c1", geom, winding))
    fpath = tmp_path / "proj.h5"

    save_project(proj, fpath)
    loaded = load_project(fpath)

    assert loaded.coils[0].winding.current == -10.0


def test_round_trip_null_creator_metadata(tmp_path: Path) -> None:
    geom = CircularGeometry(type="circular", radius=0.05)
    proj = _project(_coil("c1", geom), creatorMetadata=None)
    fpath = tmp_path / "proj.h5"

    save_project(proj, fpath)
    loaded = load_project(fpath)

    assert loaded.creatorMetadata is None


# ---------------------------------------------------------------------------
# load_project error paths
# ---------------------------------------------------------------------------


def test_load_nonexistent_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_project(tmp_path / "does_not_exist.h5")


def test_load_truncated_file_raises(tmp_path: Path) -> None:
    fpath = tmp_path / "garbage.h5"
    fpath.write_bytes(b"\x89HDF\r\nGARBAGE_DATA_NOT_VALID")
    with pytest.raises((OSError, Exception)):
        load_project(fpath)


def test_load_invalid_json_raises(tmp_path: Path) -> None:
    """Valid HDF5 layout but project_json contains malformed JSON."""
    fpath = tmp_path / "bad_json.h5"
    dt = h5py.string_dtype(encoding="utf-8")
    with h5py.File(fpath, "w") as f:
        f.attrs["schema_version"] = SCHEMA_VERSION
        f.attrs["app_version"] = "0.1.0"
        f.attrs["hdf5_format_version"] = "1"
        f.create_dataset("project_json", data="NOT { valid JSON !!!", dtype=dt)

    with pytest.raises((ValidationError, Exception)):
        load_project(fpath)


def test_load_invalid_pydantic_raises(tmp_path: Path) -> None:
    """Valid JSON but missing a required ProjectFile field (coils)."""
    bad_payload = json.dumps(
        {
            "schemaVersion": SCHEMA_VERSION,
            "appVersion": "0.1.0",
            "exportTimestamp": "2026-03-12T00:00:00Z",
            "projectName": "Bad Project",
            "displayUnits": "m",
            # "coils" intentionally missing
            "groups": [],
        }
    )
    fpath = tmp_path / "bad_pydantic.h5"
    dt = h5py.string_dtype(encoding="utf-8")
    with h5py.File(fpath, "w") as f:
        f.attrs["schema_version"] = SCHEMA_VERSION
        f.attrs["app_version"] = "0.1.0"
        f.attrs["hdf5_format_version"] = "1"
        f.create_dataset("project_json", data=bad_payload, dtype=dt)

    with pytest.raises(ValidationError):
        load_project(fpath)


# ---------------------------------------------------------------------------
# validate_import — version compatibility
# ---------------------------------------------------------------------------


def _write_file_with_version(path: Path, schema_version: str, payload: str | None = None) -> None:
    """Write a minimal valid HDF5 project file with the given schema_version attr."""
    if payload is None:
        geom = CircularGeometry(type="circular", radius=0.05)
        proj = _project(_coil("c1", geom), schemaVersion=schema_version)
        payload = proj.model_dump_json()

    dt = h5py.string_dtype(encoding="utf-8")
    with h5py.File(path, "w") as f:
        f.attrs["schema_version"] = schema_version
        f.attrs["app_version"] = "0.1.0"
        f.attrs["hdf5_format_version"] = "1"
        f.create_dataset("project_json", data=payload, dtype=dt)


def test_validate_same_version(tmp_path: Path) -> None:
    fpath = tmp_path / "proj.h5"
    _write_file_with_version(fpath, SCHEMA_VERSION)

    result = validate_import(fpath)

    assert isinstance(result, ValidationResult)
    assert result.valid is True
    assert result.issues == []


def test_validate_minor_ahead(tmp_path: Path) -> None:
    """File saved with minor version newer than current → valid with one warning."""
    major, minor, patch = (int(p) for p in SCHEMA_VERSION.split("."))
    newer_minor = f"{major}.{minor + 1}.{patch}"

    fpath = tmp_path / "proj.h5"
    geom = CircularGeometry(type="circular", radius=0.05)
    # Use current schema in the JSON payload; only the attr differs
    _write_file_with_version(fpath, newer_minor)

    result = validate_import(fpath)

    assert result.valid is True
    assert len(result.warnings) == 1
    assert len(result.errors) == 0
    assert "newer" in result.warnings[0].message.lower()


def test_validate_major_mismatch_newer(tmp_path: Path) -> None:
    """File saved with higher major version → invalid (breaking change)."""
    major, minor, patch = (int(p) for p in SCHEMA_VERSION.split("."))
    newer_major = f"{major + 1}.0.0"

    fpath = tmp_path / "proj.h5"
    _write_file_with_version(fpath, newer_major)

    result = validate_import(fpath)

    assert result.valid is False
    assert len(result.errors) == 1
    assert "incompatible" in result.errors[0].message.lower()


def test_validate_major_mismatch_older(tmp_path: Path) -> None:
    """File saved with lower major version → invalid (migration required)."""
    major, minor, patch = (int(p) for p in SCHEMA_VERSION.split("."))
    if major == 0:
        pytest.skip("Cannot test older major when current major is 0")

    older_major = f"{major - 1}.0.0"
    fpath = tmp_path / "proj.h5"
    _write_file_with_version(fpath, older_major)

    result = validate_import(fpath)

    assert result.valid is False
    assert len(result.errors) == 1


def test_validate_missing_schema_version_attr(tmp_path: Path) -> None:
    """HDF5 file without schema_version attr → invalid."""
    fpath = tmp_path / "no_version.h5"
    geom = CircularGeometry(type="circular", radius=0.05)
    proj = _project(_coil("c1", geom))

    dt = h5py.string_dtype(encoding="utf-8")
    with h5py.File(fpath, "w") as f:
        # Deliberately omit schema_version
        f.attrs["app_version"] = "0.1.0"
        f.create_dataset("project_json", data=proj.model_dump_json(), dtype=dt)

    result = validate_import(fpath)

    assert result.valid is False
    assert len(result.errors) == 1
    assert "schema_version" in result.errors[0].message.lower()


def test_validate_corrupt_json(tmp_path: Path) -> None:
    """Valid HDF5 with invalid JSON in project_json → invalid."""
    fpath = tmp_path / "corrupt.h5"
    _write_file_with_version(fpath, SCHEMA_VERSION, payload="not-json{{{")

    result = validate_import(fpath)

    assert result.valid is False
    assert any("json" in e.message.lower() for e in result.errors)


def test_validate_pydantic_invalid(tmp_path: Path) -> None:
    """Valid JSON structure but fails Pydantic validation → invalid."""
    bad_payload = json.dumps(
        {
            "schemaVersion": SCHEMA_VERSION,
            "appVersion": "0.1.0",
            "exportTimestamp": "2026-03-12T00:00:00Z",
            "projectName": "Bad",
            "displayUnits": "m",
            "coils": [{"id": "x"}],  # missing required coil fields
            "groups": [],
        }
    )
    fpath = tmp_path / "pydantic_fail.h5"
    _write_file_with_version(fpath, SCHEMA_VERSION, payload=bad_payload)

    result = validate_import(fpath)

    assert result.valid is False
    assert len(result.errors) >= 1


def test_validate_nonexistent_file(tmp_path: Path) -> None:
    result = validate_import(tmp_path / "nope.h5")

    assert result.valid is False
    assert any("not found" in e.message.lower() for e in result.errors)


def test_validate_not_hdf5(tmp_path: Path) -> None:
    """A plain text file is not a valid HDF5 file."""
    fpath = tmp_path / "not_hdf5.h5"
    fpath.write_text("this is not an HDF5 file\n")

    result = validate_import(fpath)

    assert result.valid is False


# ---------------------------------------------------------------------------
# validate_import — ValidationResult helpers
# ---------------------------------------------------------------------------


def test_validation_result_error_warning_separation(tmp_path: Path) -> None:
    """ValidationResult.errors and .warnings filter correctly."""
    # minor-ahead triggers a warning but no errors
    major, minor, patch = (int(p) for p in SCHEMA_VERSION.split("."))
    newer_minor = f"{major}.{minor + 1}.{patch}"
    fpath = tmp_path / "proj.h5"
    _write_file_with_version(fpath, newer_minor)

    result = validate_import(fpath)

    assert result.valid is True
    assert len(result.errors) == 0
    assert len(result.warnings) == 1


def test_hdf5_file_has_expected_attributes(tmp_path: Path) -> None:
    """Saved HDF5 file exposes schema_version, app_version, hdf5_format_version."""
    geom = CircularGeometry(type="circular", radius=0.05)
    proj = _project(_coil("c1", geom))
    fpath = tmp_path / "proj.h5"
    save_project(proj, fpath)

    with h5py.File(fpath, "r") as f:
        assert f.attrs["schema_version"] == SCHEMA_VERSION
        assert f.attrs["app_version"] == "0.1.0"
        assert f.attrs["hdf5_format_version"] == "1"
        assert "project_json" in f
