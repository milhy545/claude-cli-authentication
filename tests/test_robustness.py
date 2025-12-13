"""Stress and robustness tests for Claude Auth Manager."""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from claude_cli_auth.facade import ClaudeAuthManager
from claude_cli_auth.models import AuthConfig, SessionStatus
from claude_cli_auth.exceptions import ClaudeTimeoutError

@pytest.fixture
def mock_managers():
    """Mock underlying managers."""
    with patch("claude_cli_auth.facade.AuthManager") as am_mock, \
         patch("claude_cli_auth.facade.CLIInterface") as cli_mock, \
         patch("claude_cli_auth.facade.SDKInterface") as sdk_mock:

        am_instance = am_mock.return_value
        am_instance.is_authenticated.return_value = True

        yield am_instance, cli_mock, sdk_mock

@pytest.mark.asyncio
async def test_timeout_handling(mock_managers):
    """Test behavior when query times out."""
    am_mock, cli_cls, sdk_cls = mock_managers

    # Setup manager with short timeout
    config = AuthConfig(timeout_seconds=0.1)
    manager = ClaudeAuthManager(config=config, prefer_sdk=False)

    # Mock CLI to hang (simulate timeout)
    cli_instance = cli_cls.return_value
    manager.cli_interface = cli_instance

    async def delayed_execute(*args, **kwargs):
        await asyncio.sleep(0.5)
        return MagicMock()

    cli_instance.execute = AsyncMock(side_effect=delayed_execute)

    # Expect timeout error
    # Note: CLIInterface internally handles asyncio.wait_for, so it might raise ClaudeTimeoutError directly
    # or asyncio.TimeoutError depending on implementation.
    # ClaudeAuthManager catches exceptions.
    # We need to ensure CLIInterface simulates the timeout behavior correctly OR
    # check if ClaudeAuthManager wraps it.
    # Looking at CLIInterface code, it uses asyncio.wait_for and raises ClaudeTimeoutError.

    # Let's mock execute to raise ClaudeTimeoutError directly to simulate what CLIInterface does
    cli_instance.execute = AsyncMock(side_effect=ClaudeTimeoutError("Timeout"))

    with pytest.raises(ClaudeTimeoutError):
        await manager.query("Test prompt")

@pytest.mark.asyncio
async def test_invalid_session_recovery(mock_managers):
    """Test handling of invalid or expired session."""
    am_mock, cli_cls, sdk_cls = mock_managers

    manager = ClaudeAuthManager(prefer_sdk=False)
    cli_instance = cli_cls.return_value
    manager.cli_interface = cli_instance

    # Mock AuthManager to return None for session
    am_mock.get_session.return_value = None

    # When querying with non-existent session, it should probably create a new one or fail?
    # ClaudeAuthManager._get_or_create_session calls auth_manager.get_session.
    # If it returns None, it calls auth_manager.create_session.

    am_mock.create_session.return_value = MagicMock(session_id="new_session")

    # Execute
    cli_response = MagicMock()
    cli_response.to_claude_response.return_value = MagicMock(
        cost=0.0, num_turns=0, tools_used=[], session_id="new_session"
    )
    cli_instance.execute = AsyncMock(return_value=cli_response)

    response = await manager.query("Test", session_id="invalid_old_session")

    assert response is not None
    # Should have tried to create a new session
    am_mock.create_session.assert_called()

@pytest.mark.asyncio
async def test_cleanup_sessions(mock_managers):
    """Test session cleanup logic."""
    am_mock, _, _ = mock_managers

    manager = ClaudeAuthManager()

    # Mock cleanup return value
    am_mock.cleanup_expired_sessions.return_value = 5

    count = await manager.cleanup_sessions()

    assert count == 5
    am_mock.cleanup_expired_sessions.assert_called_once()
