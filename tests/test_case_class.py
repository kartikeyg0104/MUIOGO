"""Tests for CaseClass — decoupled data initialization with buffered batch writes."""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'API'))


# ---------------------------------------------------------------------------
# Minimal fixtures — mirror the structures that CaseClass expects
# ---------------------------------------------------------------------------

MINIMAL_PARAMETERS = {
    "R": [{"id": "DiscountRate", "default": 0.05}],
    "RY": [{"id": "AnnualDemand", "default": 1}],
    "RT": [],
    "RE": [],
    "RS": [],
    "RYCn": [],
    "RYTs": [],
    "RYDtb": [],
    "RYSeDt": [],
    "RYT": [],
    "RYS": [],
    "RYTCn": [],
    "RYTM": [],
    "RYC": [],
    "RYE": [],
    "RYTC": [],
    "RYTCM": [],
    "RYTSM": [],
    "RTSM": [],
    "RYTE": [],
    "RYTEM": [],
    "RYTTs": [],
    "RYCTs": [],
}

MINIMAL_GENDATA = {
    "osy-scenarios": [
        {"ScenarioId": "SC_0"},
        {"ScenarioId": "SC_1"},
    ],
    "osy-years": ["2020", "2025", "2030"],
    "osy-tech": [],
    "osy-comm": [],
    "osy-emis": [],
    "osy-stg": [],
    "osy-ts": [],
    "osy-se": [],
    "osy-dt": [],
    "osy-dtb": [],
    "osy-constraints": [],
    "osy-mo": "1",
}


@pytest.fixture
def tmp_datastorage(tmp_path):
    """Create a temporary DataStorage directory with a Parameters.json."""
    ds = tmp_path / "DataStorage"
    ds.mkdir()
    params_file = ds / "Parameters.json"
    params_file.write_text(json.dumps(MINIMAL_PARAMETERS))
    return ds


@pytest.fixture
def case_instance(tmp_datastorage):
    """Return a Case instance wired to the temporary DataStorage."""
    casename = "TestCase"
    case_dir = tmp_datastorage / casename
    case_dir.mkdir()

    with patch("Classes.Base.Config.DATA_STORAGE", tmp_datastorage):
        from Classes.Case.CaseClass import Case
        return Case(casename, MINIMAL_GENDATA)


# ---------------------------------------------------------------------------
# Tests: pure-function behaviour of default_* methods
# ---------------------------------------------------------------------------

class TestDefaultMethodsArePure:
    """default_* methods must return data and NOT write to disk."""

    def test_default_R_returns_dict(self, case_instance):
        result = case_instance.default_R()
        assert isinstance(result, dict)
        assert "DiscountRate" in result

    def test_default_R_contains_scenarios(self, case_instance):
        result = case_instance.default_R()
        dr = result["DiscountRate"]
        assert "SC_0" in dr
        assert "SC_1" in dr
        # SC_0 gets the default value
        assert dr["SC_0"][0]["value"] == 0.05
        # SC_1 gets None
        assert dr["SC_1"][0]["value"] is None

    def test_default_RY_returns_dict(self, case_instance):
        result = case_instance.default_RY()
        assert isinstance(result, dict)
        assert "AnnualDemand" in result

    def test_default_methods_do_not_touch_disk(self, case_instance, tmp_datastorage):
        """No JSON files should appear after calling a default_* method."""
        case_instance.default_R()
        case_instance.default_RY()
        case_dir = tmp_datastorage / "TestCase"
        json_files = list(case_dir.glob("*.json"))
        assert json_files == [], f"Unexpected files written: {json_files}"


# ---------------------------------------------------------------------------
# Tests: createCase buffered batch write
# ---------------------------------------------------------------------------

class TestCreateCaseBatchWrite:
    """createCase must aggregate data then flush to disk in one batch."""

    def test_creates_expected_json_files(self, case_instance, tmp_datastorage):
        case_instance.createCase()
        case_dir = tmp_datastorage / "TestCase"
        # Only groups with non-empty parameter arrays get files
        assert (case_dir / "R.json").exists()
        assert (case_dir / "RY.json").exists()

    def test_written_data_matches_returned_data(self, case_instance, tmp_datastorage):
        case_instance.createCase()
        case_dir = tmp_datastorage / "TestCase"

        with open(case_dir / "R.json") as f:
            written = json.load(f)
        expected = case_instance.default_R()
        assert written == expected

    def test_empty_groups_not_written(self, case_instance, tmp_datastorage):
        """Groups whose parameter array is empty should produce no file."""
        case_instance.createCase()
        case_dir = tmp_datastorage / "TestCase"
        # RT has an empty list in MINIMAL_PARAMETERS → no RT.json
        assert not (case_dir / "RT.json").exists()


# ---------------------------------------------------------------------------
# Tests: transactional rollback
# ---------------------------------------------------------------------------

class TestRollbackOnFailure:
    """If an IOError occurs mid-write, already-written files must be removed."""

    def test_rollback_removes_partial_files(self, case_instance, tmp_datastorage):
        case_dir = tmp_datastorage / "TestCase"

        # Import File to patch
        from Classes.Base.FileClass import File
        original_writeFile = File.writeFile

        call_count = [0]

        @staticmethod
        def failing_write(data, path):
            call_count[0] += 1
            if call_count[0] > 1:
                raise IOError("Simulated disk full")
            # First call succeeds normally
            original_writeFile(data, path)

        with patch.object(File, 'writeFile', failing_write):
            with pytest.raises(IOError):
                case_instance.createCase()

        # After rollback, NO parameter JSON files should remain
        json_files = [f.name for f in case_dir.glob("*.json")]
        assert json_files == [], f"Zombie files after rollback: {json_files}"

    def test_rollback_preserves_case_directory(self, case_instance, tmp_datastorage):
        """The case directory itself should survive a rollback (caller owns it)."""
        case_dir = tmp_datastorage / "TestCase"

        from Classes.Base.FileClass import File

        @staticmethod
        def always_fail(data, path):
            raise IOError("Simulated failure")

        with patch.object(File, 'writeFile', always_fail):
            with pytest.raises(IOError):
                case_instance.createCase()

        assert case_dir.exists(), "Case directory was incorrectly removed"
