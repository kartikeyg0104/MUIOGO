"""Tests for the /shutdown and /health routes (local-mode only)."""

import os
import sys
import signal
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'API'))

from app import app


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealthRoute:
    """Verify the /health route."""

    def test_health_returns_200(self, client):
        """GET /health should return 200 with status ok."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data.get('status') == 'ok'

    def test_health_post_not_allowed(self, client):
        """POST /health should not be allowed."""
        response = client.post('/health')
        assert response.status_code in (404, 405)


# ---------------------------------------------------------------------------
# /shutdown
# ---------------------------------------------------------------------------

class TestShutdownRoute:
    """Verify the /shutdown route behaves correctly in local mode."""

    def test_shutdown_returns_200(self, client):
        """POST /shutdown should return 200 with a message before the process
        is killed (response must be delivered before termination)."""
        with patch('threading.Timer') as mock_timer_cls:
            mock_timer_cls.return_value = MagicMock()
            response = client.post('/shutdown')
            assert response.status_code == 200
            data = response.get_json()
            assert 'message' in data
            assert 'shutting down' in data['message'].lower()

    def test_shutdown_schedules_timer(self, client):
        """POST /shutdown should schedule a timer (not kill immediately)."""
        with patch('threading.Timer') as mock_timer_cls:
            mock_instance = MagicMock()
            mock_timer_cls.return_value = mock_instance
            client.post('/shutdown')
            # A timer must be created and started
            mock_timer_cls.assert_called_once()
            mock_instance.start.assert_called_once()

    def test_shutdown_timer_sends_sigint(self, client):
        """The timer callback passed to shutdown should send SIGINT to the
        current PID — ensuring the correct signal is used with waitress."""
        captured = {}

        def capture_timer(delay, fn):
            captured['delay'] = delay
            captured['fn'] = fn
            return MagicMock()

        with patch('threading.Timer', side_effect=capture_timer):
            client.post('/shutdown')

        assert 'fn' in captured, "Timer was never created"
        assert captured['delay'] > 0, "Delay must be positive so response returns first"

        # Invoke the deferred callback and verify it sends SIGINT
        with patch('os.kill') as mock_kill:
            captured['fn']()
            mock_kill.assert_called_once_with(os.getpid(), signal.SIGINT)

    def test_shutdown_get_not_allowed(self, client):
        """GET /shutdown should not be allowed."""
        response = client.get('/shutdown')
        assert response.status_code in (404, 405)
