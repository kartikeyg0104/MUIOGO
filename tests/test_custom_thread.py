"""Tests for API.Classes.Base.CustomThreadClass."""

import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'API'))

from Classes.Base.CustomThreadClass import CustomThread


class TestCustomThread:
    """CustomThread basic functionality."""

    def test_returns_target_result(self):
        """join() should return the value produced by the target function."""
        t = CustomThread(target=lambda: 42)
        t.start()
        result = t.join()
        assert result == 42

    def test_returns_none_for_void_target(self):
        t = CustomThread(target=lambda: None)
        t.start()
        assert t.join() is None

    def test_passes_args(self):
        t = CustomThread(target=lambda a, b: a + b, args=(3, 7))
        t.start()
        assert t.join() == 10

    def test_passes_kwargs(self):
        t = CustomThread(target=lambda x=0: x * 2, kwargs={"x": 5})
        t.start()
        assert t.join() == 10

    def test_join_accepts_timeout(self):
        """Regression: join(timeout=...) must not raise TypeError."""
        def slow():
            time.sleep(0.5)
            return "done"

        t = CustomThread(target=slow)
        t.start()
        result = t.join(timeout=2)
        assert result == "done"

    def test_join_timeout_returns_before_completion(self):
        """join() with a short timeout should return without blocking forever."""
        def very_slow():
            time.sleep(10)
            return "never"

        t = CustomThread(target=very_slow)
        t.daemon = True  # so it won't block test exit
        t.start()
        t.join(timeout=0.1)
        # Thread is still alive because timeout was short
        assert t.is_alive()
