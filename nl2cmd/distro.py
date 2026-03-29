"""OS and distribution detection for adaptive package manager commands."""

from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass, field
from pathlib import Path

PACKAGE_MANAGERS: dict[str, dict[str, str]] = {
    "apt": {
        "install": "sudo apt install -y {package}",
        "remove": "sudo apt remove {package}",
        "update": "sudo apt update",
        "upgrade": "sudo apt update && sudo apt upgrade -y",
        "search": "apt search {package}",
        "list": "dpkg -l",
    },
    "dnf": {
        "install": "sudo dnf install -y {package}",
        "remove": "sudo dnf remove {package}",
        "update": "sudo dnf check-update",
        "upgrade": "sudo dnf upgrade -y",
        "search": "dnf search {package}",
        "list": "dnf list installed",
    },
    "pacman": {
        "install": "sudo pacman -S --noconfirm {package}",
        "remove": "sudo pacman -R {package}",
        "update": "sudo pacman -Sy",
        "upgrade": "sudo pacman -Syu --noconfirm",
        "search": "pacman -Ss {package}",
        "list": "pacman -Q",
    },
    "zypper": {
        "install": "sudo zypper install -y {package}",
        "remove": "sudo zypper remove {package}",
        "update": "sudo zypper refresh",
        "upgrade": "sudo zypper update -y",
        "search": "zypper search {package}",
        "list": "zypper packages --installed-only",
    },
    "apk": {
        "install": "sudo apk add {package}",
        "remove": "sudo apk del {package}",
        "update": "sudo apk update",
        "upgrade": "sudo apk upgrade",
        "search": "apk search {package}",
        "list": "apk list --installed",
    },
}

DISTRO_TO_PM: dict[str, str] = {
    "ubuntu": "apt",
    "debian": "apt",
    "linuxmint": "apt",
    "pop": "apt",
    "elementary": "apt",
    "fedora": "dnf",
    "centos": "dnf",
    "rhel": "dnf",
    "rocky": "dnf",
    "alma": "dnf",
    "arch": "pacman",
    "manjaro": "pacman",
    "endeavouros": "pacman",
    "opensuse": "zypper",
    "sles": "zypper",
    "alpine": "apk",
}


@dataclass
class DistroInfo:
    """Detected distribution information."""

    name: str = "linux"
    id: str = "linux"
    version: str = ""
    package_manager: str = "apt"
    pm_commands: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.pm_commands:
            self.pm_commands = PACKAGE_MANAGERS.get(self.package_manager, PACKAGE_MANAGERS["apt"])


def detect_distro() -> DistroInfo:
    """Detect the current Linux distribution and package manager."""
    os_release = Path("/etc/os-release")
    info: dict[str, str] = {}

    if os_release.exists():
        for line in os_release.read_text().splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                info[key] = value.strip('"')

    distro_id = info.get("ID", "linux").lower()
    distro_name = info.get("PRETTY_NAME", info.get("NAME", platform.system()))
    distro_version = info.get("VERSION_ID", "")

    # Determine package manager
    pm = DISTRO_TO_PM.get(distro_id, "")
    if not pm:
        # Fallback: check which package manager binary exists
        for pm_name in ("apt", "dnf", "pacman", "zypper", "apk"):
            if shutil.which(pm_name):
                pm = pm_name
                break
        else:
            pm = "apt"  # Default fallback

    return DistroInfo(
        name=distro_name,
        id=distro_id,
        version=distro_version,
        package_manager=pm,
        pm_commands=PACKAGE_MANAGERS.get(pm, PACKAGE_MANAGERS["apt"]),
    )
