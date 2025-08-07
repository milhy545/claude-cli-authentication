"""Basic tests for claude-cli-auth module."""

import pytest
from unittest.mock import Mock, patch

from claude_cli_auth import ClaudeAuthManager, AuthConfig
from claude_cli_auth.exceptions import ClaudeAuthError


def test_imports():
    """Test that all main components can be imported."""
    from claude_cli_auth import (
        ClaudeAuthManager,
        AuthManager,
        CLIInterface,
        SDKInterface,
        AuthConfig,
        ClaudeResponse,
        SessionInfo,
        StreamUpdate,
        ClaudeAuthError
    )
    
    assert ClaudeAuthManager is not None
    assert AuthConfig is not None
    assert ClaudeAuthError is not None


def test_auth_config():
    """Test AuthConfig creation and defaults."""
    config = AuthConfig()
    
    assert config.timeout_seconds == 30
    assert config.session_timeout_hours == 24
    assert config.use_sdk is True
    assert config.enable_streaming is True
    
    # Test custom config
    custom_config = AuthConfig(
        timeout_seconds=60,
        session_timeout_hours=48,
        use_sdk=False
    )
    
    assert custom_config.timeout_seconds == 60
    assert custom_config.session_timeout_hours == 48
    assert custom_config.use_sdk is False


def test_claude_auth_manager_init():
    """Test ClaudeAuthManager initialization."""
    manager = ClaudeAuthManager()
    
    assert manager is not None
    assert manager.auth_manager is not None
    assert hasattr(manager, 'list_sessions')
    assert hasattr(manager, 'get_session')


@patch('claude_cli_auth.auth_manager.AuthManager.is_authenticated')
def test_authentication_check(mock_is_authenticated):
    """Test authentication status check."""
    mock_is_authenticated.return_value = True
    
    manager = ClaudeAuthManager()
    is_auth = manager.auth_manager.is_authenticated()
    
    assert is_auth is True
    mock_is_authenticated.assert_called_once()


def test_claude_response_model():
    """Test ClaudeResponse model."""
    from claude_cli_auth.models import ClaudeResponse
    
    response = ClaudeResponse(
        content="Test response",
        session_id="test-session",
        cost=0.01,
        duration_ms=1000,
        num_turns=1,
        tools_used=["test_tool"]
    )
    
    assert response.content == "Test response"
    assert response.session_id == "test-session"
    assert response.cost == 0.01
    assert response.duration_ms == 1000
    assert response.num_turns == 1
    assert response.tools_used == ["test_tool"]


def test_session_info_model():
    """Test SessionInfo model."""
    from claude_cli_auth.models import SessionInfo, SessionStatus
    from datetime import datetime
    
    now = datetime.now()
    session = SessionInfo(
        session_id="test-session",
        created_at=now,
        last_used=now,
        total_cost=0.05,
        total_turns=3,
        status=SessionStatus.ACTIVE
    )
    
    assert session.session_id == "test-session"
    assert session.created_at == now
    assert session.last_used == now
    assert session.total_cost == 0.05
    assert session.total_turns == 3
    assert session.status == SessionStatus.ACTIVE


def test_exceptions_hierarchy():
    """Test exception hierarchy."""
    from claude_cli_auth.exceptions import (
        ClaudeAuthError,
        ClaudeCLIError,
        ClaudeTimeoutError,
        ClaudeSessionError
    )
    
    # Test inheritance
    assert issubclass(ClaudeCLIError, ClaudeAuthError)
    assert issubclass(ClaudeTimeoutError, ClaudeAuthError)
    assert issubclass(ClaudeSessionError, ClaudeAuthError)
    
    # Test exception creation
    error = ClaudeAuthError("Test error", suggestions=["Try again"])
    assert str(error) == "Test error"
    assert error.suggestions == ["Try again"]