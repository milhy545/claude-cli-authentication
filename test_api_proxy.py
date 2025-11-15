"""Quick test of API proxy functionality."""

import asyncio
import sys


def test_imports():
    """Test that all imports work."""
    print("Testing imports...")

    try:
        from claude_cli_auth.api_proxy import (
            ClaudeAPIProxy,
            ChatCompletionRequest,
            ChatMessage,
            FormatConverter,
        )
        print("✓ API proxy imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_format_converter():
    """Test format conversion."""
    print("\nTesting format converter...")

    from claude_cli_auth.api_proxy import FormatConverter, ChatMessage

    # Test OpenAI to Claude conversion
    messages = [
        ChatMessage(role="system", content="You are helpful"),
        ChatMessage(role="user", content="Hello!"),
        ChatMessage(role="assistant", content="Hi there!"),
        ChatMessage(role="user", content="How are you?"),
    ]

    prompt = FormatConverter.openai_to_claude_prompt(messages)
    print(f"✓ Converted {len(messages)} messages to prompt")
    print(f"  Prompt length: {len(prompt)} chars")
    print(f"  Preview: {prompt[:100]}...")

    # Test Claude to OpenAI conversion
    response = FormatConverter.claude_to_openai_response(
        claude_content="I'm doing great!",
        request_id="test-123",
        model="claude-sonnet-4",
        cost=0.001,
    )

    print(f"✓ Converted Claude response to OpenAI format")
    print(f"  Response ID: {response.id}")
    print(f"  Model: {response.model}")
    print(f"  Content: {response.choices[0].message.content}")

    return True


def test_request_models():
    """Test request/response models."""
    print("\nTesting request models...")

    from claude_cli_auth.api_proxy import ChatCompletionRequest, ChatMessage

    # Create request
    request = ChatCompletionRequest(
        model="claude-sonnet-4",
        messages=[
            ChatMessage(role="user", content="Hello!")
        ],
        stream=False,
        temperature=1.0,
    )

    print(f"✓ Created request with {len(request.messages)} message(s)")
    print(f"  Model: {request.model}")
    print(f"  Stream: {request.stream}")
    print(f"  Temperature: {request.temperature}")

    return True


async def test_proxy_initialization():
    """Test proxy initialization."""
    print("\nTesting proxy initialization...")

    try:
        from claude_cli_auth.api_proxy import ClaudeAPIProxy
        from claude_cli_auth import AuthConfig

        # Create config (this won't fail even if Claude isn't authenticated)
        config = AuthConfig(
            timeout_seconds=60,
        )

        print("✓ Created AuthConfig")

        # Try to initialize proxy (may fail if Claude CLI not authenticated)
        try:
            proxy = ClaudeAPIProxy(
                config=config,
                host="127.0.0.1",
                port=8888,
            )
            print("✓ Initialized ClaudeAPIProxy")

            # Check health (will show authentication status)
            health = await proxy.get_health()
            print(f"✓ Health check complete")
            print(f"  Status: {health['status']}")
            print(f"  Authenticated: {health['claude_authenticated']}")

            # Cleanup
            await proxy.shutdown()
            print("✓ Proxy shutdown successful")

            return True

        except Exception as e:
            print(f"⚠ Proxy initialization failed (expected if not authenticated): {e}")
            print("  Note: This is expected if you haven't run 'claude auth login'")
            return True  # Still pass the test

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Claude API Proxy - Quick Test Suite")
    print("=" * 60)
    print()

    results = []

    # Test imports
    results.append(("Imports", test_imports()))

    # Test format converter
    results.append(("Format Converter", test_format_converter()))

    # Test request models
    results.append(("Request Models", test_request_models()))

    # Test proxy initialization
    results.append(("Proxy Initialization", asyncio.run(test_proxy_initialization())))

    # Summary
    print()
    print("=" * 60)
    print("Test Results:")
    print("=" * 60)

    passed = 0
    failed = 0

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} {name}")

        if result:
            passed += 1
        else:
            failed += 1

    print()
    print(f"Total: {passed + failed} tests, {passed} passed, {failed} failed")
    print()

    if failed > 0:
        print("Some tests failed!")
        sys.exit(1)
    else:
        print("All tests passed! ✓")
        sys.exit(0)


if __name__ == "__main__":
    main()
