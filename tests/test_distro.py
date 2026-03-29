"""Tests for distro detection."""

from nl2cmd.distro import DistroInfo, PACKAGE_MANAGERS


class TestDistroInfo:
    def test_default_pm_commands(self):
        info = DistroInfo()
        assert info.package_manager == "apt"
        assert "install" in info.pm_commands

    def test_custom_pm(self):
        info = DistroInfo(package_manager="pacman")
        assert info.pm_commands == PACKAGE_MANAGERS["pacman"]

    def test_pm_install_template(self):
        info = DistroInfo(package_manager="apt")
        cmd = info.pm_commands["install"].format(package="nginx")
        assert "nginx" in cmd
        assert "apt" in cmd
