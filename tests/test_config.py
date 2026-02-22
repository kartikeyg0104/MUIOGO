"""Tests for API.Classes.Base.Config — validate configuration constants."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'API'))

from Classes.Base import Config


class TestParametersCIntegrity:
    """Verify PARAMETERS_C has correct dimension keys."""

    def test_emission_activity_ratio_dimensions(self):
        """Regression: 'e''t' string concatenation typo must be fixed."""
        dims = Config.PARAMETERS_C['EmissionActivityRatio']
        assert dims == ['r', 'e', 't', 'y', 'm'], (
            f"EmissionActivityRatio dimensions are wrong: {dims}"
        )

    def test_all_dimension_keys_are_single_chars_or_known(self):
        """Every dimension key should be a short known identifier."""
        known = {'r', 'f', 't', 'y', 'm', 'e', 'l', 's', 'rr', 'cn',
                 'ls', 'ld', 'lh'}
        for param, dims in Config.PARAMETERS_C.items():
            for d in dims:
                assert d in known, (
                    f"Unexpected dimension key '{d}' in PARAMETERS_C['{param}']"
                )


class TestConfigPaths:
    """Verify that configured paths are pathlib.Path objects."""

    def test_data_storage_is_path(self):
        from pathlib import Path
        assert isinstance(Config.DATA_STORAGE, Path)

    def test_solvers_folder_is_path(self):
        from pathlib import Path
        assert isinstance(Config.SOLVERs_FOLDER, Path)


class TestConfigGroups:
    """Sanity-check that group tuples are non-empty."""

    def test_tech_groups_non_empty(self):
        assert len(Config.TECH_GROUPS) > 0

    def test_comm_groups_non_empty(self):
        assert len(Config.COMM_GROUPS) > 0

    def test_emis_groups_non_empty(self):
        assert len(Config.EMIS_GROUPS) > 0


class TestDefaultUpdateGenMappings:
    """DEFAULT_F, UPDATE_F, and GEN_F must have the same keys."""

    def test_default_and_update_keys_match(self):
        assert set(Config.DEFAULT_F.keys()) == set(Config.UPDATE_F.keys())

    def test_default_and_gen_keys_match(self):
        assert set(Config.DEFAULT_F.keys()) == set(Config.GEN_F.keys())
