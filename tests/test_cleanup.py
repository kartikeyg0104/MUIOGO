"""Tests for DataFile.cleanUp handling of non-directory files in resultsPath."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'API'))

from unittest.mock import patch
from pathlib import Path

from Classes.Case.DataFileClass import DataFile


def _make_cleanup_instance(results_path, view_folder_path):
    """Create a DataFile instance with only the attributes cleanUp() needs,
    bypassing the heavy Osemosys.__init__ constructor."""
    instance = object.__new__(DataFile)
    instance.resultsPath = results_path
    instance.viewFolderPath = view_folder_path
    return instance


@pytest.fixture
def cleanup_env(tmp_path):
    """Set up a minimal directory structure for cleanUp tests."""
    results = tmp_path / "res"
    results.mkdir()
    view = tmp_path / "view"
    view.mkdir()
    # cleanUp writes viewDefinitions.json and reads Variables.json
    variables = {"group": [{"id": "v1"}]}
    variables_path = tmp_path / "Variables.json"
    variables_path.write_text(json.dumps(variables), encoding="utf-8")
    return results, view, variables_path


class TestCleanUpWithNonDirFiles:
    """Verify cleanUp handles non-directory files (e.g. .DS_Store) in resultsPath."""

    def test_ds_store_does_not_break_cleanup(self, cleanup_env):
        results, view, variables_path = cleanup_env

        # Create a case run directory with a file inside
        run_dir = results / "run1"
        run_dir.mkdir()
        (run_dir / "output.csv").write_text("data", encoding="utf-8")

        # Create .DS_Store at resultsPath root (the problematic file)
        (results / ".DS_Store").write_text("", encoding="utf-8")

        instance = _make_cleanup_instance(results, view)

        with patch("Classes.Base.Config.DATA_STORAGE", variables_path.parent):
            response = instance.cleanUp()

        assert response["status_code"] == "success"
        # .DS_Store should be removed
        assert not (results / ".DS_Store").exists()
        # run directory contents should be cleaned
        assert not (run_dir / "output.csv").exists()

    def test_cleanup_succeeds_with_only_directories(self, cleanup_env):
        results, view, variables_path = cleanup_env

        run_dir = results / "run1"
        run_dir.mkdir()
        (run_dir / "result.txt").write_text("x", encoding="utf-8")

        instance = _make_cleanup_instance(results, view)

        with patch("Classes.Base.Config.DATA_STORAGE", variables_path.parent):
            response = instance.cleanUp()

        assert response["status_code"] == "success"
        assert not (run_dir / "result.txt").exists()

    def test_multiple_non_dir_files_cleaned(self, cleanup_env):
        results, view, variables_path = cleanup_env

        # Create several stray files at resultsPath root
        for name in [".DS_Store", "Thumbs.db", ".gitkeep"]:
            (results / name).write_text("", encoding="utf-8")

        # Also create a normal run directory
        run_dir = results / "run1"
        run_dir.mkdir()

        instance = _make_cleanup_instance(results, view)

        with patch("Classes.Base.Config.DATA_STORAGE", variables_path.parent):
            response = instance.cleanUp()

        assert response["status_code"] == "success"
        for name in [".DS_Store", "Thumbs.db", ".gitkeep"]:
            assert not (results / name).exists()

    def test_view_folder_preserves_resdata(self, cleanup_env):
        results, view, variables_path = cleanup_env

        # resData.json should NOT be deleted
        (view / "resData.json").write_text("{}", encoding="utf-8")
        (view / "other.json").write_text("{}", encoding="utf-8")

        instance = _make_cleanup_instance(results, view)

        with patch("Classes.Base.Config.DATA_STORAGE", variables_path.parent):
            response = instance.cleanUp()

        assert response["status_code"] == "success"
        assert (view / "resData.json").exists()
        assert not (view / "other.json").exists()
