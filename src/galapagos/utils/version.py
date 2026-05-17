"""Version string normalization and display utilities."""
from __future__ import annotations


def normalize_version(version: str) -> str:
    """
    Normalize version strings to the standard underscore format.
    Examples:
        "v1.15.4" -> "v1_15_4"
        "V1.15.4" -> "v1_15_4"
        "1.15.4"  -> "v1_15_4"
        "v1_15_4" -> "v1_15_4"
    """
    v = version.lower()
    if not v.startswith("v"):
        v = "v" + v
    return v.replace(".", "_")


def display_version(version: str) -> str:
    """
    Format version strings to the standard display format.
    Examples:
        "v1_15_4" -> "V1.15.4"
        "1.15.4"  -> "V1.15.4"
        "V1.15.4" -> "V1.15.4"
    """
    v = version.upper()
    if not v.startswith("V"):
        v = "V" + v
    return v.replace("_", ".")
