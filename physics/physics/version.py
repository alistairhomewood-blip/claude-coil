"""
Version constants for the coil geometry physics package and project file schema.

Versioning policy:
  SCHEMA_VERSION  — bump MINOR when adding optional fields or relaxing constraints;
                    bump MAJOR when removing fields or making breaking changes.
  APP_VERSION     — mirrors [project].version in pyproject.toml.
  HDF5_FORMAT_VERSION — internal HDF5 file layout version (not the schema version).
                        Increment when the dataset/attribute layout changes.
"""

SCHEMA_VERSION: str = "1.0.0"
APP_VERSION: str = "0.1.0"
HDF5_FORMAT_VERSION: str = "1"
