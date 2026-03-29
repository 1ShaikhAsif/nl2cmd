"""Dangerous command detection and safety warnings."""

from __future__ import annotations

import re
from dataclasses import dataclass

DANGEROUS_PATTERNS: list[tuple[str, str]] = [
    (r"\brm\s+(-\w*f\w*\s+)*-\w*r|-\w*r\w*\s+(-\w*f|/)", "Recursive forced delete — can destroy entire directory trees"),
    (r"\brm\s+-rf\s+/", "Deleting from root — will destroy the entire filesystem"),
    (r"\bdd\s+", "Low-level disk copy — can overwrite entire disks or partitions"),
    (r"\bmkfs\b", "Format filesystem — will erase all data on the target device"),
    (r"\bchmod\s+777\b", "World-writable permissions — major security vulnerability"),
    (r">\s*/dev/sd[a-z]", "Writing directly to raw disk device"),
    (r":\(\)\s*\{\s*:\|:&\s*\}\s*;:", "Fork bomb — will crash the system by exhausting resources"),
    (r"\bcurl\b.*\|\s*(ba)?sh", "Piping remote script to shell — could execute anything"),
    (r"\bwget\b.*\|\s*(ba)?sh", "Piping remote script to shell — could execute anything"),
    (r"\bmv\s+/", "Moving files from root — can break the system"),
    (r"\b>\s*/dev/null\s+2>&1.*&\s*$", "Silently backgrounding a process — output is discarded"),
    (r"\bkill\s+-9\s+-1\b", "Kill all processes — will terminate everything including your session"),
    (r"\bshutdown\b|\breboot\b|\binit\s+[06]\b", "System shutdown/reboot"),
]


@dataclass
class SafetyResult:
    """Result of a safety check on a command."""

    is_dangerous: bool
    warnings: list[str]
    command: str

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


def check_command(command: str) -> SafetyResult:
    """Check a command for dangerous patterns.

    Returns a SafetyResult with any warnings found.
    """
    warnings: list[str] = []

    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            warnings.append(description)

    return SafetyResult(
        is_dangerous=len(warnings) > 0,
        warnings=warnings,
        command=command,
    )
