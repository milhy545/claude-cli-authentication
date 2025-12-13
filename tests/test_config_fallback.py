"""Unit tests for Configuration and Fallback logic."""

import pytest
import shutil
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

from claude_cli_auth.models import AuthConfig
from claude_cli_auth.facade import ClaudeAuthManager, SDK_AVAILABLE
from claude_cli_auth.exceptions import ClaudeConfigError, ClaudeAuthError, ClaudeAuthManagerError

# --- Configuration Tests ---

def test_config_defaults():
    """Test default configuration values."""
    config = AuthConfig()
    assert config.timeout_seconds == 120
    assert config.use_sdk is True
    assert config.claude_config_dir == Path.home() / ".claude"

def test_config_validation_valid():
    """Test validation of a valid configuration."""
    # We use temporary directory to ensure paths exist
    config = AuthConfig(
        claude_config_dir=Path("."),
        working_directory=Path("."),
        timeout_seconds=60
    )
    issues = config.validate()
    assert len(issues) == 0

def test_config_validation_invalid_paths():
    """Test validation with non-existent paths."""
    config = AuthConfig(
        claude_config_dir=Path("/non/existent/path/123"),
        working_directory=Path("/non/existent/path/456")
    )
    issues = config.validate()
    assert len(issues) >= 2
    assert any("Claude config directory not found" in i for i in issues)
    assert any("Working directory does not exist" in i for i in issues)

def test_config_validation_invalid_values():
    """Test validation with invalid numeric values."""
    config = AuthConfig(
        timeout_seconds=-1,
        max_turns=0,
        session_timeout_hours=-5.0
    )
    issues = config.validate()
    assert len(issues) >= 3
    assert any("timeout_seconds must be positive" in i for i in issues)
    assert any("max_turns must be positive" in i for i in issues)
    assert any("session_timeout_hours must be positive" in i for i in issues)

# --- Fallback Logic Tests ---

@pytest.fixture
def mock_auth_manager_cls():
    """Mock AuthManager class to avoid real disk/auth checks."""
    with patch("claude_cli_auth.facade.AuthManager") as mock:
        mock_instance = mock.return_value
        # Mock successful initialization
        mock_instance.is_authenticated.return_value = True
        yield mock

@pytest.fixture
def mock_sdk_interface():
    """Mock SDK Interface."""
    with patch("claude_cli_auth.facade.SDKInterface") as mock:
        yield mock

@pytest.fixture
def mock_cli_interface():
    """Mock CLI Interface."""
    with patch("claude_cli_auth.facade.CLIInterface") as mock:
        yield mock

@pytest.fixture
def enable_sdk_available():
    """Force SDK_AVAILABLE to True for tests."""
    with patch("claude_cli_auth.facade.SDK_AVAILABLE", True):
        yield

@pytest.mark.asyncio
async def test_manager_init_success(mock_auth_manager_cls):
    """Test successful initialization of ClaudeAuthManager."""
    manager = ClaudeAuthManager()
    assert manager.auth_manager is not None

@pytest.mark.asyncio
async def test_fallback_sdk_to_cli(
    enable_sdk_available,
    mock_auth_manager_cls,
    mock_sdk_interface,
    mock_cli_interface
):
    """Test automatic fallback from SDK to CLI when SDK fails."""

    # Setup manager with fallback enabled
    manager = ClaudeAuthManager(prefer_sdk=True, enable_fallback=True)

    # Mock SDK to raise an exception
    sdk_instance = mock_sdk_interface.return_value
    sdk_instance.execute = AsyncMock(side_effect=Exception("SDK Crash"))

    # Mock CLI to succeed
    cli_instance = mock_cli_interface.return_value
    cli_response = MagicMock()
    # Mocking to_claude_response to return a plain object, NOT a coroutine
    cli_response.to_claude_response.return_value = MagicMock(
        cost=0.1, num_turns=1, tools_used=[], session_id="test_sess"
    )
    cli_instance.execute = AsyncMock(return_value=cli_response)

    # Manually ensure both interfaces are "initialized" on the manager
    manager.sdk_interface = sdk_instance
    manager.cli_interface = cli_instance

    # Execute query
    response = await manager.query("Test prompt")

    # Verifications
    assert response is not None
    # SDK should have been called
    sdk_instance.execute.assert_called_once()
    # CLI should have been called as fallback
    cli_instance.execute.assert_called_once()

    # Stats should reflect failure and fallback
    stats = manager.get_stats()
    assert stats["sdk_failures"] == 1
    assert stats["fallback_successes"] == 1

@pytest.mark.asyncio
async def test_fallback_disabled(
    enable_sdk_available,
    mock_auth_manager_cls,
    mock_sdk_interface,
    mock_cli_interface
):
    """Test that fallback does NOT occur when disabled."""

    manager = ClaudeAuthManager(prefer_sdk=True, enable_fallback=False)

    # Mock SDK to raise an exception
    sdk_instance = mock_sdk_interface.return_value
    sdk_instance.execute = AsyncMock(side_effect=ClaudeAuthError("SDK Auth Fail"))

    # Mock CLI (should not be called)
    cli_instance = mock_cli_interface.return_value
    cli_instance.execute = AsyncMock()

    manager.sdk_interface = sdk_instance
    manager.cli_interface = cli_instance

    # Expect failure
    with pytest.raises(ClaudeAuthError):
        await manager.query("Test prompt")

    # SDK called
    sdk_instance.execute.assert_called_once()
    # CLI NOT called
    cli_instance.execute.assert_not_called()

@pytest.mark.asyncio
async def test_all_methods_fail(
    enable_sdk_available,
    mock_auth_manager_cls,
    mock_sdk_interface,
    mock_cli_interface
):
    """Test behavior when both SDK and CLI fail."""

    manager = ClaudeAuthManager(prefer_sdk=True, enable_fallback=True)

    sdk_instance = mock_sdk_interface.return_value
    sdk_instance.execute = AsyncMock(side_effect=Exception("SDK Error"))

    cli_instance = mock_cli_interface.return_value
    cli_instance.execute = AsyncMock(side_effect=Exception("CLI Error"))

    manager.sdk_interface = sdk_instance
    manager.cli_interface = cli_instance

    # Expect ClaudeAuthManagerError (wrapper for all methods failed)
    with pytest.raises(ClaudeAuthManagerError) as exc_info:
        await manager.query("Test prompt")

    assert "All Claude methods failed" in str(exc_info.value)
