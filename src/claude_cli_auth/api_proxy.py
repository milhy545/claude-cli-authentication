"""OpenAI-compatible API proxy for Claude subscription access.

This module provides an OpenAI-compatible REST API that uses Claude subscription
authentication instead of API keys. It allows tools like Claude Code to connect
using your subscription instead of paying for API access.

Features:
- OpenAI-compatible /v1/chat/completions endpoint
- Streaming support (SSE)
- Session management
- Cost tracking
- Multiple concurrent requests
- Health checks

Example usage:
    Start the server:
    ```bash
    claude-api-proxy --port 8000 --host 0.0.0.0
    ```

    Use with curl:
    ```bash
    curl http://localhost:8000/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{
        "model": "claude-sonnet-4",
        "messages": [{"role": "user", "content": "Hello!"}],
        "stream": false
      }'
    ```

    Use with OpenAI client:
    ```python
    from openai import OpenAI

    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="dummy-key"  # Not validated, but required by client
    )

    response = client.chat.completions.create(
        model="claude-sonnet-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    ```
"""

import argparse
import asyncio
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from .facade import ClaudeAuthManager
from .models import AuthConfig, StreamType, StreamUpdate

logger = logging.getLogger(__name__)


# ===== OpenAI-compatible Request/Response Models =====


class ChatMessage(BaseModel):
    """Chat message in OpenAI format."""

    role: str = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Optional name of the message author")


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""

    model: str = Field(
        default="claude-sonnet-4",
        description="Model to use (mapped to Claude models)"
    )
    messages: List[ChatMessage] = Field(..., description="List of messages")
    temperature: Optional[float] = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum tokens to generate"
    )
    stream: bool = Field(default=False, description="Whether to stream responses")
    user: Optional[str] = Field(None, description="User identifier for tracking")


class ChatCompletionChoice(BaseModel):
    """Single completion choice."""

    index: int
    message: ChatMessage
    finish_reason: str  # "stop", "length", "error"


class ChatCompletionUsage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[ChatCompletionUsage] = None


class ChatCompletionChunk(BaseModel):
    """Streaming chat completion chunk."""

    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]


class ErrorResponse(BaseModel):
    """Error response."""

    error: Dict[str, Any]


# ===== Format Converters =====


class FormatConverter:
    """Convert between OpenAI and Claude formats."""

    @staticmethod
    def openai_to_claude_prompt(messages: List[ChatMessage]) -> str:
        """Convert OpenAI messages to Claude prompt.

        Args:
            messages: List of OpenAI chat messages

        Returns:
            Combined prompt string for Claude
        """
        # Combine all messages into a single prompt
        # Claude CLI works best with a single prompt string
        prompt_parts = []

        for msg in messages:
            role = msg.role
            content = msg.content

            if role == "system":
                prompt_parts.append(f"System Instructions: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        return "\n\n".join(prompt_parts)

    @staticmethod
    def claude_to_openai_response(
        claude_content: str,
        request_id: str,
        model: str,
        cost: float = 0.0,
    ) -> ChatCompletionResponse:
        """Convert Claude response to OpenAI format.

        Args:
            claude_content: Response content from Claude
            request_id: Request identifier
            model: Model name used
            cost: Cost in USD

        Returns:
            OpenAI-compatible response
        """
        # Estimate tokens from cost (approximate)
        # Claude Sonnet costs roughly $3/M input, $15/M output
        estimated_tokens = int(cost * 100000) if cost > 0 else 0

        return ChatCompletionResponse(
            id=request_id,
            object="chat.completion",
            created=int(time.time()),
            model=model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant",
                        content=claude_content
                    ),
                    finish_reason="stop"
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=estimated_tokens // 3,
                completion_tokens=estimated_tokens * 2 // 3,
                total_tokens=estimated_tokens,
            )
        )

    @staticmethod
    def stream_update_to_chunk(
        update: StreamUpdate,
        request_id: str,
        model: str,
    ) -> Optional[ChatCompletionChunk]:
        """Convert Claude stream update to OpenAI chunk.

        Args:
            update: Claude stream update
            request_id: Request identifier
            model: Model name

        Returns:
            OpenAI-compatible chunk or None if not relevant
        """
        # Only convert assistant messages to chunks
        if update.type != StreamType.ASSISTANT:
            return None

        if not update.content:
            return None

        return ChatCompletionChunk(
            id=request_id,
            object="chat.completion.chunk",
            created=int(time.time()),
            model=model,
            choices=[{
                "index": 0,
                "delta": {"content": update.content},
                "finish_reason": None
            }]
        )


# ===== API Proxy Server =====


class ClaudeAPIProxy:
    """OpenAI-compatible API proxy for Claude subscription access."""

    def __init__(
        self,
        config: Optional[AuthConfig] = None,
        host: str = "127.0.0.1",
        port: int = 8000,
    ):
        """Initialize API proxy.

        Args:
            config: Claude authentication configuration
            host: Host to bind to
            port: Port to bind to
        """
        self.config = config or AuthConfig()
        self.host = host
        self.port = port

        # Initialize Claude manager
        self.claude = ClaudeAuthManager(config=self.config)

        # Request tracking
        self.active_requests: Dict[str, asyncio.Task] = {}

        # Stats
        self.stats = {
            "total_requests": 0,
            "streaming_requests": 0,
            "failed_requests": 0,
            "total_cost": 0.0,
        }

        logger.info(
            f"ClaudeAPIProxy initialized - host: {host}, port: {port}, "
            f"config: {self.config.to_dict()}"
        )

    async def handle_chat_completion(
        self,
        request: ChatCompletionRequest,
    ):
        """Handle chat completion request.

        Args:
            request: Chat completion request

        Returns:
            Response or streaming response (ChatCompletionResponse or StreamingResponse)

        Raises:
            HTTPException: If request fails
        """
        request_id = f"chatcmpl-{uuid.uuid4()}"

        logger.info(
            f"Handling chat completion - request_id: {request_id}, "
            f"model: {request.model}, stream: {request.stream}, "
            f"messages: {len(request.messages)}, user: {request.user}"
        )

        # Update stats
        self.stats["total_requests"] += 1
        if request.stream:
            self.stats["streaming_requests"] += 1

        try:
            # Convert OpenAI format to Claude prompt
            prompt = FormatConverter.openai_to_claude_prompt(request.messages)

            # Handle streaming vs non-streaming
            if request.stream:
                return await self._handle_streaming(
                    prompt=prompt,
                    request_id=request_id,
                    model=request.model,
                    user=request.user,
                )
            else:
                return await self._handle_non_streaming(
                    prompt=prompt,
                    request_id=request_id,
                    model=request.model,
                    user=request.user,
                )

        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(
                f"Chat completion failed - request_id: {request_id}, "
                f"error: {str(e)}, error_type: {type(e).__name__}"
            )

            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "message": str(e),
                        "type": type(e).__name__,
                        "code": "internal_error"
                    }
                }
            )

    async def _handle_non_streaming(
        self,
        prompt: str,
        request_id: str,
        model: str,
        user: Optional[str] = None,
    ) -> ChatCompletionResponse:
        """Handle non-streaming request.

        Args:
            prompt: Claude prompt
            request_id: Request identifier
            model: Model name
            user: User identifier

        Returns:
            Chat completion response
        """
        # Execute Claude query
        response = await self.claude.query(
            prompt=prompt,
            user_id=user,
        )

        # Update stats
        self.stats["total_cost"] += response.cost

        # Convert to OpenAI format
        return FormatConverter.claude_to_openai_response(
            claude_content=response.content,
            request_id=request_id,
            model=model,
            cost=response.cost,
        )

    async def _handle_streaming(
        self,
        prompt: str,
        request_id: str,
        model: str,
        user: Optional[str] = None,
    ) -> StreamingResponse:
        """Handle streaming request.

        Args:
            prompt: Claude prompt
            request_id: Request identifier
            model: Model name
            user: User identifier

        Returns:
            Streaming response
        """
        # Use a queue to pass updates from callback to generator
        update_queue: asyncio.Queue = asyncio.Queue()

        async def stream_callback(update: StreamUpdate) -> None:
            """Handle stream updates from Claude."""
            await update_queue.put(update)

        async def event_generator() -> AsyncIterator[str]:
            """Generate SSE events."""
            try:
                # Start Claude query task
                query_task = asyncio.create_task(
                    self.claude.query(
                        prompt=prompt,
                        user_id=user,
                        stream_callback=stream_callback,
                    )
                )

                # Process updates as they arrive
                while True:
                    try:
                        # Wait for update with timeout
                        update = await asyncio.wait_for(
                            update_queue.get(),
                            timeout=0.1
                        )

                        # Convert to OpenAI chunk
                        chunk = FormatConverter.stream_update_to_chunk(
                            update=update,
                            request_id=request_id,
                            model=model,
                        )

                        if chunk:
                            yield f"data: {chunk.model_dump_json()}\n\n"

                    except asyncio.TimeoutError:
                        # Check if query is done
                        if query_task.done():
                            break
                        continue

                # Wait for final result
                response = await query_task

                # Update stats
                self.stats["total_cost"] += response.cost

                # Send final chunk with finish_reason
                final_chunk = ChatCompletionChunk(
                    id=request_id,
                    object="chat.completion.chunk",
                    created=int(time.time()),
                    model=model,
                    choices=[{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                )

                yield f"data: {final_chunk.model_dump_json()}\n\n"
                yield "data: [DONE]\n\n"

            except Exception as e:
                logger.error(
                    f"Streaming error - request_id: {request_id}, error: {str(e)}"
                )

                # Send error chunk
                error_chunk = {
                    "error": {
                        "message": str(e),
                        "type": type(e).__name__,
                        "code": "stream_error"
                    }
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"

        return EventSourceResponse(event_generator())

    async def get_health(self) -> Dict[str, Any]:
        """Get health status.

        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy" if self.claude.is_healthy() else "unhealthy",
            "claude_authenticated": self.claude.auth_manager.is_authenticated(),
            "stats": self.stats,
            "active_requests": len(self.active_requests),
        }

    async def shutdown(self) -> None:
        """Shutdown the proxy."""
        logger.info("Shutting down ClaudeAPIProxy")

        # Cancel active requests
        for task in self.active_requests.values():
            task.cancel()

        # Shutdown Claude manager
        await self.claude.shutdown()

        logger.info("ClaudeAPIProxy shutdown complete")


# ===== FastAPI Application =====


# Global proxy instance
proxy: Optional[ClaudeAPIProxy] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global proxy

    # Startup
    logger.info("Starting ClaudeAPIProxy server")
    yield

    # Shutdown
    if proxy:
        await proxy.shutdown()


app = FastAPI(
    title="Claude API Proxy",
    description="OpenAI-compatible API proxy for Claude subscription access",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/v1/chat/completions", response_model=None)
async def chat_completions(
    request: ChatCompletionRequest,
):
    """OpenAI-compatible chat completions endpoint.

    Args:
        request: Chat completion request

    Returns:
        Chat completion response or streaming response
    """
    global proxy

    if not proxy:
        raise HTTPException(
            status_code=503,
            detail="Proxy not initialized"
        )

    return await proxy.handle_chat_completion(request)


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint.

    Returns:
        Health status
    """
    global proxy

    if not proxy:
        return {
            "status": "unhealthy",
            "error": "Proxy not initialized"
        }

    return await proxy.get_health()


@app.get("/v1/models")
async def list_models() -> Dict[str, Any]:
    """List available models (OpenAI-compatible).

    Returns:
        List of models
    """
    return {
        "object": "list",
        "data": [
            {
                "id": "claude-sonnet-4",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "anthropic",
            },
            {
                "id": "claude-opus-4",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "anthropic",
            },
        ]
    }


# ===== CLI =====


def main() -> None:
    """Main entry point for API proxy CLI."""
    parser = argparse.ArgumentParser(
        description="Claude API Proxy - OpenAI-compatible API using Claude subscription"
    )

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Query timeout in seconds (default: 120)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create config
    config = AuthConfig(
        timeout_seconds=args.timeout,
    )

    # Initialize proxy
    global proxy
    proxy = ClaudeAPIProxy(
        config=config,
        host=args.host,
        port=args.port,
    )

    logger.info(
        f"Starting Claude API Proxy on {args.host}:{args.port}\n"
        f"OpenAI-compatible endpoint: http://{args.host}:{args.port}/v1/chat/completions\n"
        f"Health check: http://{args.host}:{args.port}/health\n"
        f"API docs: http://{args.host}:{args.port}/docs"
    )

    # Run server
    import uvicorn
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info" if not args.debug else "debug",
    )


if __name__ == "__main__":
    main()
