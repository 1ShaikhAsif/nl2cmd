"""Shared utility functions."""

from __future__ import annotations

import re
import shlex

# Filesize units mapping to find -size suffixes
FILESIZE_UNITS: dict[str, str] = {
    "b": "c",      # bytes
    "kb": "k",
    "k": "k",
    "mb": "M",
    "m": "M",
    "gb": "G",
    "g": "G",
    "tb": "T",
    "t": "T",
}


def parse_filesize(text: str) -> str:
    """Parse a human-readable filesize into a find-compatible size string.

    Examples:
        "1gb" -> "1G"
        "500mb" -> "500M"
        "100M" -> "100M"
    """
    match = re.match(r"(\d+)\s*([a-zA-Z]+)", text.strip())
    if not match:
        return text
    number, unit = match.group(1), match.group(2).lower()
    suffix = FILESIZE_UNITS.get(unit, unit.upper())
    return f"{number}{suffix}"


def parse_duration(text: str) -> str:
    """Parse a human-readable duration into days (for find -mtime).

    Examples:
        "7 days" -> "7"
        "2 weeks" -> "14"
        "1 month" -> "30"
    """
    match = re.match(r"(\d+)\s*(day|week|month|hour|minute|min)s?", text.strip().lower())
    if not match:
        return text
    number, unit = int(match.group(1)), match.group(2)
    multipliers = {"day": 1, "week": 7, "month": 30, "hour": 0, "minute": 0, "min": 0}
    days = number * multipliers.get(unit, 1)
    return str(max(days, 1))


def parse_port(text: str) -> str:
    """Extract a port number from text.

    Examples:
        "port 3000" -> "3000"
        "8080" -> "8080"
    """
    match = re.search(r"\b(\d{1,5})\b", text)
    return match.group(1) if match else text


def sanitize_input(text: str) -> str:
    """Sanitize user input for safe shell usage.

    Uses shlex.quote to properly escape the input.
    """
    return shlex.quote(text)


def is_tty() -> bool:
    """Check if stdout is connected to a terminal."""
    import sys
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


SLOT_PARSERS: dict[str, callable] = {
    "filesize": parse_filesize,
    "duration": parse_duration,
    "port": parse_port,
    "path": lambda x: x.strip(),
    "package": lambda x: x.strip(),
    "filename": lambda x: x.strip(),
    "string": lambda x: x.strip(),
    "number": lambda x: re.search(r"\d+", x).group(0) if re.search(r"\d+", x) else x,
}
