"""Unit tests for CLI interface parsing using mock data."""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from claude_cli_auth.cli_interface import CLIInterface, CLIResponse
from claude_cli_auth.models import StreamType, StreamUpdate, AuthConfig

# Mock data based on provided patterns
MOCK_ASSISTANT_MSG = {
    "type": "assistant",
    "message": {
        "content": [{"type": "text", "text": "Ahoj, jak ti mohu pomoci?"}],
        "role": "assistant"
    },
    "session_id": "uuid-session-123",
    "id": "msg_123"
}

MOCK_TOOL_USE_MSG = {
    "type": "assistant",
    "message": {
        "content": [
            {
                "type": "tool_use",
                "name": "ReadFile",
                "input": {"path": "main.py"},
                "id": "tool_call_xyz"
            }
        ],
        "role": "assistant"
    },
    "session_id": "uuid-session-123",
    "id": "msg_124"
}

MOCK_RESULT_MSG = {
    "type": "result",
    "result": "Obsah souboru main.py je...",
    "cost_usd": 0.0015,
    "duration_ms": 450,
    "num_turns": 2,
    "is_error": False,
    "session_id": "uuid-session-123"
}

MOCK_ERROR_MSG = {
    "type": "error",
    "error": {
        "type": "overloaded_error",
        "message": "Claude is currently overloaded"
    },
    "session_id": "uuid-session-123"
}

@pytest.fixture
def cli_interface():
    # Mock AuthManager to bypass authentication check
    mock_auth = MagicMock()
    mock_auth.is_authenticated.return_value = True

    interface = CLIInterface(auth_manager=mock_auth)
    return interface

@pytest.mark.asyncio
async def test_parse_assistant_message(cli_interface):
    """Test parsing of standard assistant text message."""
    update = cli_interface._create_stream_update(MOCK_ASSISTANT_MSG)

    assert update is not None
    assert update.type == StreamType.ASSISTANT
    assert update.content == "Ahoj, jak ti mohu pomoci?"
    assert update.session_id == "uuid-session-123"
    assert update.metadata.get("message_id") == "msg_123"

@pytest.mark.asyncio
async def test_parse_tool_use_message(cli_interface):
    """Test parsing of tool use message."""
    update = cli_interface._create_stream_update(MOCK_TOOL_USE_MSG)

    assert update is not None
    assert update.type == StreamType.ASSISTANT
    assert update.tool_calls is not None
    assert len(update.tool_calls) == 1

    tool_call = update.tool_calls[0]
    assert tool_call["name"] == "ReadFile"
    assert tool_call["input"] == {"path": "main.py"}
    assert tool_call["id"] == "tool_call_xyz"

@pytest.mark.asyncio
async def test_parse_error_update(cli_interface):
    """Test parsing of error message."""
    update = cli_interface._create_stream_update(MOCK_ERROR_MSG)

    assert update is not None
    assert update.type == StreamType.ERROR
    assert "Claude is currently overloaded" in update.content
    assert update.error_info["message"] == "Claude is currently overloaded"

@pytest.mark.asyncio
async def test_handle_process_output_success(cli_interface):
    """Test full output handling with success sequence."""

    # Create a mock process with stdout
    mock_process = AsyncMock()
    mock_process.wait.return_value = 0

    # Setup mock stdout stream
    # Sequence: Assistant msg -> Tool use -> Result
    mock_lines = [
        json.dumps(MOCK_ASSISTANT_MSG),
        json.dumps(MOCK_TOOL_USE_MSG),
        json.dumps(MOCK_RESULT_MSG)
    ]

    # Mock _read_stream_bounded to yield lines
    async def mock_read_stream(stream):
        for line in mock_lines:
            yield line

    with patch.object(cli_interface, '_read_stream_bounded', side_effect=mock_read_stream):
        # We need a callback to capture stream updates
        updates = []
        async def callback(update):
            updates.append(update)

        response = await cli_interface._handle_process_output(
            process=mock_process,
            stream_callback=callback,
            process_id="test_proc"
        )

        # Verify response
        assert isinstance(response, CLIResponse)
        assert response.content == "Obsah souboru main.py je..."
        assert response.session_id == "uuid-session-123"
        assert response.cost == 0.0015
        assert response.is_error is False

        # Verify stream updates were captured
        assert len(updates) == 2  # Assistant + Tool Use (Result is not a stream update usually, or handled internally)
        assert updates[0].type == StreamType.ASSISTANT
        assert updates[1].type == StreamType.ASSISTANT
        assert updates[1].tool_calls[0]["name"] == "ReadFile"

        # Verify tools_used in response (extracted from messages)
        # The logic in _parse_result_message reconstructs tools from buffered messages
        assert len(response.tools_used) == 1
        assert response.tools_used[0]["name"] == "ReadFile"

@pytest.mark.asyncio
async def test_handle_process_output_error(cli_interface):
    """Test handling of process failure output."""
    mock_process = AsyncMock()
    mock_process.wait.return_value = 1
    mock_process.stderr.read.return_value = b"Error: Usage limit reached reset at 10pm"

    # Mock _read_stream_bounded to yield empty or partial
    async def mock_read_stream(stream):
        yield ""

    with patch.object(cli_interface, '_read_stream_bounded', side_effect=mock_read_stream):
        # Should raise ClaudeCLIError
        from claude_cli_auth.exceptions import ClaudeCLIError

        with pytest.raises(ClaudeCLIError) as exc_info:
            await cli_interface._handle_process_output(
                process=mock_process,
                stream_callback=None,
                process_id="test_proc_err"
            )

        assert "usage limit reached" in str(exc_info.value).lower()
