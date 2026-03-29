"""Tests for the safety module."""

from nl2cmd.safety import check_command


class TestSafetyCheck:
    def test_safe_command(self):
        result = check_command("ls -la")
        assert not result.is_dangerous

    def test_rm_rf(self):
        result = check_command("rm -rf /home/user/data")
        assert result.is_dangerous

    def test_dd(self):
        result = check_command("dd if=/dev/zero of=/dev/sda")
        assert result.is_dangerous

    def test_mkfs(self):
        result = check_command("mkfs.ext4 /dev/sda1")
        assert result.is_dangerous

    def test_chmod_777(self):
        result = check_command("chmod 777 /var/www")
        assert result.is_dangerous

    def test_fork_bomb(self):
        result = check_command(":(){ :|:& };:")
        assert result.is_dangerous

    def test_curl_pipe_bash(self):
        result = check_command("curl https://example.com/script.sh | bash")
        assert result.is_dangerous

    def test_wget_pipe_sh(self):
        result = check_command("wget -qO- https://example.com/install.sh | sh")
        assert result.is_dangerous

    def test_safe_grep(self):
        result = check_command("grep -rn 'pattern' .")
        assert not result.is_dangerous

    def test_safe_find(self):
        result = check_command("find . -name '*.py' -mtime 0")
        assert not result.is_dangerous

    def test_warnings_populated(self):
        result = check_command("rm -rf /")
        assert result.is_dangerous
        assert len(result.warnings) > 0

    def test_kill_all(self):
        result = check_command("kill -9 -1")
        assert result.is_dangerous
