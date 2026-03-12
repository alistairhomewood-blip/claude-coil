"""
Pytest configuration and shared fixtures.

Reference-case JSON files live in /tests/reference-cases/ (project root).
Load them here so individual test modules can parametrize against them.
"""

import json
import pathlib
import pytest

# Path to the project-root reference-cases directory
REFERENCE_CASES_DIR = (
    pathlib.Path(__file__).parent.parent.parent / "tests" / "reference-cases"
)


def load_reference_case(filename: str) -> dict:
    """Load a reference-case JSON fixture by filename."""
    path = REFERENCE_CASES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Reference case not found: {path}")
    return json.loads(path.read_text())


@pytest.fixture
def single_circular_loop() -> dict:
    return load_reference_case("single_circular_loop.json")


@pytest.fixture
def helmholtz_coil() -> dict:
    return load_reference_case("helmholtz_coil.json")


@pytest.fixture
def toroidal_solenoid() -> dict:
    return load_reference_case("toroidal_solenoid.json")


@pytest.fixture
def racetrack_coil() -> dict:
    return load_reference_case("racetrack_coil.json")


@pytest.fixture
def packing_check() -> dict:
    return load_reference_case("packing_check.json")


@pytest.fixture
def toroidal_poloidal_winding() -> dict:
    return load_reference_case("toroidal_poloidal_winding.json")


@pytest.fixture
def toroidal_toroidal_winding() -> dict:
    return load_reference_case("toroidal_toroidal_winding.json")


@pytest.fixture
def elongated_toroidal_poloidal_winding() -> dict:
    return load_reference_case("elongated_toroidal_poloidal_winding.json")


@pytest.fixture
def elongated_toroidal_toroidal_winding() -> dict:
    return load_reference_case("elongated_toroidal_toroidal_winding.json")
