"""Tests for API.Classes.Base.FileClass."""

import json
import os
import tempfile

import pytest

# Allow imports from API/ directory
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'API'))

from Classes.Base.FileClass import File


@pytest.fixture
def tmp_json(tmp_path):
    """Return a helper that writes raw text to a temp .json file."""
    def _make(data, filename="test.json"):
        path = tmp_path / filename
        path.write_text(json.dumps(data), encoding="utf-8")
        return path
    return _make


class TestReadFile:
    """File.readFile round-trip tests."""

    def test_reads_valid_json(self, tmp_json):
        payload = {"key": "value", "nums": [1, 2, 3]}
        path = tmp_json(payload)
        result = File.readFile(path)
        assert result == payload

    def test_reads_nested_json(self, tmp_json):
        payload = {"a": {"b": {"c": 42}}}
        path = tmp_json(payload)
        assert File.readFile(path) == payload

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises((IOError, OSError)):
            File.readFile(tmp_path / "nonexistent.json")

    def test_raises_on_invalid_json(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(Exception):
            File.readFile(bad)


class TestWriteFile:
    """File.writeFile round-trip tests."""

    def test_write_then_read(self, tmp_path):
        payload = {"x": 1, "arr": [10, 20]}
        path = tmp_path / "out.json"
        File.writeFile(payload, path)
        assert File.readFile(path) == payload

    def test_overwrites_existing(self, tmp_path):
        path = tmp_path / "out.json"
        File.writeFile({"v": 1}, path)
        File.writeFile({"v": 2}, path)
        assert File.readFile(path)["v"] == 2

    def test_writes_pretty_printed(self, tmp_path):
        path = tmp_path / "out.json"
        File.writeFile({"a": 1}, path)
        raw = path.read_text(encoding="utf-8")
        # indent=4 produces multi-line output
        assert "\n" in raw


class TestWriteFileUJson:
    """File.writeFileUJson round-trip tests."""

    def test_write_then_read(self, tmp_path):
        payload = {"compact": True}
        path = tmp_path / "compact.json"
        File.writeFileUJson(payload, path)
        assert File.readFile(path) == payload


class TestReadParamFile:
    """File.readParamFile tests."""

    def test_reads_valid_json(self, tmp_json):
        payload = [{"id": "p1", "value": "v1"}]
        path = tmp_json(payload)
        assert File.readParamFile(path) == payload

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises((IOError, OSError)):
            File.readParamFile(tmp_path / "missing.json")
