"""Claude CLI Authentication Module.

A production-ready Python module for Claude AI integration without API keys.
Uses Claude CLI authentication for seamless access to Claude Code capabilities.

Key Features:
- No API keys required (uses `claude auth login`)
- Works with Claude subscription instead of API access
- Triple fallback system (SDK → CLI → Error handling)
- Session persistence and management
- Production-ready error handling
- Memory optimized streaming

Example:
    Basic usage:
    
    ```python
    from claude_cli_auth import ClaudeAuthManager
    from pathlib import Path
    
    claude = ClaudeAuthManager()
    response = await claude.query(
        "Explain this code",
        working_directory=Path(".")
    )
    print(response.content)
    ```

    With session management:
    
    ```python
    # Start conversation
    response = await claude.query(
        "Create a Python function",
        session_id="my-session"
    )
    
    # Continue conversation
    response = await claude.query(
        "Add error handling to that function",
        session_id="my-session",
        continue_session=True
    )
    ```
"""

from .auth_manager import AuthManager
from .cli_interface import CLIInterface, CLIResponse
from .exceptions import (
    ClaudeAuthError,
    ClaudeAuthManagerError,
    ClaudeCLIError,
    ClaudeConfigError,
    ClaudeNetworkError,
    ClaudeParsingError,
    ClaudeRateLimitError,
    ClaudeSessionError,
    ClaudeTimeoutError,
    ClaudeToolValidationError,
)
from .facade import ClaudeAuthManager
from .models import AuthConfig, ClaudeResponse, SessionInfo, StreamUpdate
from .sdk_interface import SDKInterface

# API Proxy is optional - only import if FastAPI is available
try:
    from .api_proxy import ClaudeAPIProxy, ChatCompletionRequest, ChatMessage
    _API_PROXY_AVAILABLE = True
except ImportError:
    _API_PROXY_AVAILABLE = False
    ClaudeAPIProxy = None  # type: ignore
    ChatCompletionRequest = None  # type: ignore
    ChatMessage = None  # type: ignore

# Version info
__version__ = "1.0.0"
__author__ = "David Strejc"
__email__ = "strejc.david@gmail.com"
__license__ = "MIT"

# Public API
__all__ = [
    # Main interface
    "ClaudeAuthManager",

    # Core components
    "AuthManager",
    "CLIInterface",
    "SDKInterface",

    # API Proxy (optional)
    "ClaudeAPIProxy",
    "ChatCompletionRequest",
    "ChatMessage",

    # Models
    "AuthConfig",
    "ClaudeResponse",
    "CLIResponse",
    "SessionInfo",
    "StreamUpdate",

    # Exceptions
    "ClaudeAuthError",
    "ClaudeAuthManagerError",
    "ClaudeCLIError",
    "ClaudeConfigError",
    "ClaudeNetworkError",
    "ClaudeParsingError",
    "ClaudeRateLimitError",
    "ClaudeSessionError",
    "ClaudeTimeoutError",
    "ClaudeToolValidationError",

    # Metadata
    "__version__",
    "__author__",
    "__email__",
    "__license__",
]

# Module-level configuration
import logging
import os

# Set up default logging if not configured
if not logging.getLogger(__name__).handlers:
    logging.basicConfig(
        level=logging.INFO if os.getenv("CLAUDE_DEBUG") else logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

# Disable debug logging for dependencies by default
for logger_name in ["httpx", "asyncio", "urllib3"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)