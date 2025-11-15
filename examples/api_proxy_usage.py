"""Example usage of Claude API Proxy.

This example demonstrates how to use the Claude API Proxy to access Claude
via subscription instead of API keys, using OpenAI-compatible interfaces.
"""

import asyncio
from pathlib import Path


# ===== Example 1: Start the proxy server =====
def example_start_server():
    """Example: Start the API proxy server."""
    print("=" * 60)
    print("Example 1: Start the API Proxy Server")
    print("=" * 60)
    print()
    print("To start the proxy server, run:")
    print()
    print("  claude-api-proxy --host 0.0.0.0 --port 8000")
    print()
    print("Or with custom timeout:")
    print()
    print("  claude-api-proxy --host 0.0.0.0 --port 8000 --timeout 300")
    print()
    print("The server will be available at:")
    print("  - API endpoint: http://localhost:8000/v1/chat/completions")
    print("  - Health check: http://localhost:8000/health")
    print("  - API docs: http://localhost:8000/docs")
    print()


# ===== Example 2: Use with curl =====
def example_curl_usage():
    """Example: Use the proxy with curl."""
    print("=" * 60)
    print("Example 2: Use with curl")
    print("=" * 60)
    print()
    print("Non-streaming request:")
    print()
    print("""curl http://localhost:8000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "claude-sonnet-4",
    "messages": [
      {"role": "user", "content": "Hello! How are you?"}
    ],
    "stream": false
  }'""")
    print()
    print("Streaming request:")
    print()
    print("""curl http://localhost:8000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "claude-sonnet-4",
    "messages": [
      {"role": "user", "content": "Write a Python function to calculate fibonacci"}
    ],
    "stream": true
  }'""")
    print()


# ===== Example 3: Use with OpenAI Python client =====
def example_openai_client():
    """Example: Use the proxy with OpenAI Python client."""
    print("=" * 60)
    print("Example 3: Use with OpenAI Python Client")
    print("=" * 60)
    print()
    print("First, install the OpenAI client:")
    print()
    print("  pip install openai")
    print()
    print("Then use it like this:")
    print()
    print("""from openai import OpenAI

# Initialize client pointing to your proxy
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy-key"  # Not validated, but required by client
)

# Non-streaming request
response = client.chat.completions.create(
    model="claude-sonnet-4",
    messages=[
        {"role": "user", "content": "Hello! How are you?"}
    ]
)

print(response.choices[0].message.content)

# Streaming request
stream = client.chat.completions.create(
    model="claude-sonnet-4",
    messages=[
        {"role": "user", "content": "Write a Python function"}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
""")
    print()


# ===== Example 4: Use with Claude Code =====
def example_claude_code():
    """Example: Use the proxy with Claude Code."""
    print("=" * 60)
    print("Example 4: Use with Claude Code")
    print("=" * 60)
    print()
    print("To use the proxy with Claude Code, you need to configure it")
    print("to use a custom API endpoint.")
    print()
    print("1. Start the proxy server:")
    print("   claude-api-proxy --host 0.0.0.0 --port 8000")
    print()
    print("2. Configure Claude Code to use custom endpoint:")
    print("   (This depends on how Claude Code is configured)")
    print()
    print("   You might need to set environment variables like:")
    print("   export ANTHROPIC_API_URL=http://localhost:8000/v1")
    print("   export ANTHROPIC_API_KEY=dummy-key")
    print()
    print("3. Use Claude Code as normal!")
    print()


# ===== Example 5: Use with LangChain =====
def example_langchain():
    """Example: Use the proxy with LangChain."""
    print("=" * 60)
    print("Example 5: Use with LangChain")
    print("=" * 60)
    print()
    print("You can use the proxy with LangChain by using the OpenAI integration:")
    print()
    print("""from langchain_openai import ChatOpenAI

# Initialize LangChain with your proxy
llm = ChatOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy-key",
    model="claude-sonnet-4"
)

# Use as normal
response = llm.invoke("Hello! How are you?")
print(response.content)

# Streaming
for chunk in llm.stream("Write a Python function"):
    print(chunk.content, end="")
""")
    print()


# ===== Example 6: Programmatic usage =====
async def example_programmatic():
    """Example: Programmatic usage of the proxy."""
    print("=" * 60)
    print("Example 6: Programmatic Usage")
    print("=" * 60)
    print()
    print("You can also use the proxy programmatically in your Python code:")
    print()
    print("""from claude_cli_auth import ClaudeAuthManager
from claude_cli_auth.api_proxy import ClaudeAPIProxy, ChatCompletionRequest, ChatMessage

# Initialize proxy
proxy = ClaudeAPIProxy(
    host="127.0.0.1",
    port=8000
)

# Create request
request = ChatCompletionRequest(
    model="claude-sonnet-4",
    messages=[
        ChatMessage(role="user", content="Hello!")
    ],
    stream=False
)

# Handle request
response = await proxy.handle_chat_completion(request)

print(response.choices[0].message.content)

# Shutdown
await proxy.shutdown()
""")
    print()


# ===== Example 7: Health check =====
def example_health_check():
    """Example: Health check endpoint."""
    print("=" * 60)
    print("Example 7: Health Check")
    print("=" * 60)
    print()
    print("Check if the proxy is healthy:")
    print()
    print("  curl http://localhost:8000/health")
    print()
    print("Example response:")
    print("""{
  "status": "healthy",
  "claude_authenticated": true,
  "stats": {
    "total_requests": 42,
    "streaming_requests": 15,
    "failed_requests": 2,
    "total_cost": 0.125
  },
  "active_requests": 0
}""")
    print()


# ===== Example 8: List models =====
def example_list_models():
    """Example: List available models."""
    print("=" * 60)
    print("Example 8: List Available Models")
    print("=" * 60)
    print()
    print("Get list of available models:")
    print()
    print("  curl http://localhost:8000/v1/models")
    print()
    print("Example response:")
    print("""{
  "object": "list",
  "data": [
    {
      "id": "claude-sonnet-4",
      "object": "model",
      "created": 1699564800,
      "owned_by": "anthropic"
    },
    {
      "id": "claude-opus-4",
      "object": "model",
      "created": 1699564800,
      "owned_by": "anthropic"
    }
  ]
}""")
    print()


# ===== Main =====
def main():
    """Run all examples."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "Claude API Proxy - Usage Examples" + " " * 15 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    example_start_server()
    input("Press Enter to continue...")
    print()

    example_curl_usage()
    input("Press Enter to continue...")
    print()

    example_openai_client()
    input("Press Enter to continue...")
    print()

    example_claude_code()
    input("Press Enter to continue...")
    print()

    example_langchain()
    input("Press Enter to continue...")
    print()

    asyncio.run(example_programmatic())
    input("Press Enter to continue...")
    print()

    example_health_check()
    input("Press Enter to continue...")
    print()

    example_list_models()
    print()

    print("=" * 60)
    print("All examples shown!")
    print("=" * 60)
    print()
    print("To get started:")
    print("  1. Install: pip install claude-cli-auth")
    print("  2. Authenticate: claude auth login")
    print("  3. Start proxy: claude-api-proxy --port 8000")
    print("  4. Use with any OpenAI-compatible tool!")
    print()


if __name__ == "__main__":
    main()
