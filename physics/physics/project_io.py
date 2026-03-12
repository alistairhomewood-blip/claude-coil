"""
HDF5 save/load library for the coil geometry project file.

Public API
----------
save_project(project, path)         → None
load_project(path)                  → ProjectFile
validate_import(path)               → ValidationResult

HDF5 file layout (format version "1")
--------------------------------------
/ (root)
├── attrs:
│   ├── schema_version       str  e.g. "1.0.0"
│   ├── app_version          str  e.g. "0.1.0"
│   └── hdf5_format_version  str  "1"
└── project_json             dataset (UTF-8 string)

The entire ProjectFile is serialised as a single UTF-8 JSON string.  Large
numerical arrays (B-field grids, filament paths) will go in sibling datasets
in a future layout version.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import h5py
from pydantic import ValidationError

from .types import ProjectFile
from .version import APP_VERSION, HDF5_FORMAT_VERSION, SCHEMA_VERSION


# ---------------------------------------------------------------------------
# Validation result types
# ---------------------------------------------------------------------------


@dataclass
class ValidationIssue:
    level: Literal["error", "warning"]
    message: str

    def __str__(self) -> str:
        return f"[{self.level.upper()}] {self.message}"


@dataclass
class ValidationResult:
    """
    Result of validate_import().

    valid  — True when there are no errors (warnings are acceptable).
    issues — Ordered list of ValidationIssue objects.
    """

    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "warning"]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_semver(version_str: str) -> tuple[int, int, int]:
    """Parse a 'MAJOR.MINOR.PATCH' string. Raises ValueError on bad input."""
    parts = version_str.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"Expected semver MAJOR.MINOR.PATCH, got: {version_str!r}")
    try:
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        raise ValueError(f"Non-integer semver component in: {version_str!r}")


def _read_schema_version_attr(h5file: h5py.File) -> str | None:
    """Read the schema_version root attribute. Returns None if absent."""
    raw = h5file.attrs.get("schema_version")
    if raw is None:
        return None
    # h5py may return bytes
    return raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)


def _read_project_json(h5file: h5py.File) -> str:
    """Read the project_json dataset as a Python str."""
    ds = h5file["project_json"]
    raw = ds.asstr()[()]  # returns str directly for string-dtype datasets
    return raw


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def save_project(project: ProjectFile, path: str | Path) -> None:
    """
    Serialise *project* to an HDF5 file at *path*.

    Creates the file (or overwrites an existing one).  The file is written
    atomically via h5py's default buffering; partial writes on crash are not
    guaranteed to be safe — callers that need atomicity should write to a
    temporary path and rename.

    Parameters
    ----------
    project : ProjectFile
        Fully-validated project model to persist.
    path : str | Path
        Destination file path.  Parent directory must already exist.
    """
    path = Path(path)
    project_json: str = project.model_dump_json()

    with h5py.File(path, "w") as f:
        # Root-level attributes allow version checks without parsing JSON
        f.attrs["schema_version"] = project.schemaVersion
        f.attrs["app_version"] = project.appVersion
        f.attrs["hdf5_format_version"] = HDF5_FORMAT_VERSION

        # Store the full serialised project
        dt = h5py.string_dtype(encoding="utf-8")
        ds = f.create_dataset("project_json", data=project_json, dtype=dt)
        ds.attrs["description"] = (
            "Full ProjectFile serialised as JSON (UTF-8). "
            "Parse with physics.project_io.load_project()."
        )


def load_project(path: str | Path) -> ProjectFile:
    """
    Load and validate a ProjectFile from an HDF5 file.

    Parameters
    ----------
    path : str | Path
        Path to the .h5 project file.

    Returns
    -------
    ProjectFile
        Fully-validated Pydantic model.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    OSError
        If *path* is not a valid HDF5 file.
    pydantic.ValidationError
        If the stored JSON does not conform to the ProjectFile schema.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Project file not found: {path}")

    with h5py.File(path, "r") as f:
        raw_json = _read_project_json(f)

    return ProjectFile.model_validate_json(raw_json)


def validate_import(path: str | Path) -> ValidationResult:
    """
    Check import compatibility of an HDF5 project file without fully committing
    to loading it.  Returns a :class:`ValidationResult` with all errors and
    warnings collected — callers decide whether to proceed.

    Compatibility rules
    -------------------
    * Missing ``schema_version`` attribute → **error** (cannot determine compatibility).
    * File major > current major → **error** (breaking schema change).
    * File major < current major → **error** (too old; migration required).
    * File minor > current minor → **warning** (newer optional fields may be ignored).
    * Malformed JSON in ``project_json`` → **error**.
    * Pydantic validation failure → **error** per validation issue.

    Parameters
    ----------
    path : str | Path
        Path to the .h5 project file.

    Returns
    -------
    ValidationResult
        ``valid`` is True iff there are no errors (warnings are acceptable).
    """
    path = Path(path)
    issues: list[ValidationIssue] = []

    def _err(msg: str) -> None:
        issues.append(ValidationIssue(level="error", message=msg))

    def _warn(msg: str) -> None:
        issues.append(ValidationIssue(level="warning", message=msg))

    # --- Step 1: open file ---------------------------------------------------
    if not path.exists():
        _err(f"File not found: {path}")
        return ValidationResult(valid=False, issues=issues)

    try:
        h5file = h5py.File(path, "r")
    except OSError as exc:
        _err(f"Cannot open file as HDF5: {exc}")
        return ValidationResult(valid=False, issues=issues)

    with h5file:
        # --- Step 2: read schema_version attr --------------------------------
        file_version_str = _read_schema_version_attr(h5file)

        if file_version_str is None:
            _err(
                "Missing 'schema_version' attribute in HDF5 root. "
                "The file may be corrupt or not a coil geometry project file."
            )
            return ValidationResult(valid=False, issues=issues)

        try:
            file_major, file_minor, _file_patch = _parse_semver(file_version_str)
        except ValueError as exc:
            _err(f"Cannot parse schema_version {file_version_str!r}: {exc}")
            return ValidationResult(valid=False, issues=issues)

        current_major, current_minor, _ = _parse_semver(SCHEMA_VERSION)

        # --- Step 3: version compatibility check -----------------------------
        if file_major != current_major:
            _err(
                f"Incompatible schema version: file is {file_version_str}, "
                f"this application supports major version {current_major}.x.x. "
                f"{'File is too new — upgrade the application.' if file_major > current_major else 'File is too old — migration required.'}"
            )
            return ValidationResult(valid=False, issues=issues)

        if file_minor > current_minor:
            _warn(
                f"File was saved with schema version {file_version_str} which is "
                f"newer than the current {SCHEMA_VERSION}. "
                f"Unknown fields will be ignored; some features may be unavailable."
            )

        # --- Step 4: read and parse JSON -------------------------------------
        if "project_json" not in h5file:
            _err("Missing 'project_json' dataset. The file may be corrupt.")
            return ValidationResult(valid=False, issues=issues)

        try:
            raw_json = _read_project_json(h5file)
        except Exception as exc:
            _err(f"Cannot read project_json dataset: {exc}")
            return ValidationResult(valid=False, issues=issues)

    # (h5file closed) ---------------------------------------------------------

    try:
        json.loads(raw_json)
    except json.JSONDecodeError as exc:
        _err(f"project_json contains malformed JSON: {exc}")
        return ValidationResult(valid=False, issues=issues)

    # --- Step 5: Pydantic validation -----------------------------------------
    try:
        ProjectFile.model_validate_json(raw_json)
    except ValidationError as exc:
        for e in exc.errors():
            loc = " → ".join(str(p) for p in e["loc"])
            _err(f"Schema validation failed at '{loc}': {e['msg']}")

    valid = not any(i.level == "error" for i in issues)
    return ValidationResult(valid=valid, issues=issues)
