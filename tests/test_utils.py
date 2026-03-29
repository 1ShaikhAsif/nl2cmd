"""Tests for utility functions."""

from nl2cmd.utils import parse_duration, parse_filesize, parse_port


class TestParseFilesize:
    def test_gigabytes(self):
        assert parse_filesize("1gb") == "1G"

    def test_megabytes(self):
        assert parse_filesize("500mb") == "500M"

    def test_kilobytes(self):
        assert parse_filesize("100kb") == "100k"

    def test_terabytes(self):
        assert parse_filesize("2tb") == "2T"

    def test_short_form(self):
        assert parse_filesize("100M") == "100M"

    def test_with_spaces(self):
        assert parse_filesize("1 gb") == "1G"


class TestParseDuration:
    def test_days(self):
        assert parse_duration("7 days") == "7"

    def test_weeks(self):
        assert parse_duration("2 weeks") == "14"

    def test_months(self):
        assert parse_duration("1 month") == "30"

    def test_singular(self):
        assert parse_duration("1 day") == "1"


class TestParsePort:
    def test_plain_number(self):
        assert parse_port("3000") == "3000"

    def test_port_prefix(self):
        assert parse_port("port 8080") == "8080"

    def test_in_sentence(self):
        assert parse_port("on port 443") == "443"
