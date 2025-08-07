#!/usr/bin/env python3
"""Basic usage examples for claude-cli-auth module."""

import asyncio
from pathlib import Path
from claude_cli_auth import ClaudeAuthManager, AuthConfig


async def basic_query_example():
    """Basic query example."""
    print("🔥 Basic Query Example")
    print("-" * 30)
    
    # Initialize with default settings
    claude = ClaudeAuthManager()
    
    # Simple query
    response = await claude.query(
        "What is the capital of France? Answer briefly."
    )
    
    print(f"Response: {response.content}")
    print(f"Cost: ${response.cost:.4f}")
    print(f"Duration: {response.duration_ms}ms")
    
    await claude.shutdown()


async def session_management_example():
    """Session management example."""
    print("\n💬 Session Management Example")
    print("-" * 35)
    
    claude = ClaudeAuthManager()
    
    # Start a conversation
    print("Starting conversation...")
    response1 = await claude.query(
        "I'm building a Python web app. What framework should I use?",
        session_id="web-dev-chat"
    )
    print(f"Response 1: {response1.content[:100]}...")
    
    # Continue the conversation
    print("\nContinuing conversation...")
    response2 = await claude.query(
        "Great! Can you show me a simple Flask example?",
        session_id="web-dev-chat",
        continue_session=True
    )
    print(f"Response 2: {response2.content[:100]}...")
    
    # Show session info
    session_info = claude.get_session("web-dev-chat")
    if session_info:
        print(f"\nSession info:")
        print(f"  - Total turns: {session_info.total_turns}")
        print(f"  - Total cost: ${session_info.total_cost:.4f}")
        print(f"  - Status: {session_info.status.value}")
    
    await claude.shutdown()


async def file_context_example():
    """File context example."""
    print("\n📁 File Context Example")
    print("-" * 30)
    
    # Create a sample Python file
    sample_file = Path("sample.py")
    sample_file.write_text("""
def calculate_area(radius):
    # Calculate area of a circle
    return 3.14 * radius * radius

# Test the function
result = calculate_area(5)
print(f"Area: {result}")
""")
    
    claude = ClaudeAuthManager()
    
    # Query with file context
    response = await claude.query(
        "Review this Python code and suggest improvements",
        files=[sample_file],
        working_directory=Path(".")
    )
    
    print(f"Code review: {response.content}")
    
    # Clean up
    sample_file.unlink()
    await claude.shutdown()


async def custom_config_example():
    """Custom configuration example."""
    print("\n⚙️ Custom Configuration Example")
    print("-" * 38)
    
    # Custom configuration
    config = AuthConfig(
        timeout_seconds=60,           # Longer timeout
        session_timeout_hours=48,     # Longer session lifetime  
        use_sdk=False,               # Force CLI usage
        enable_streaming=True         # Enable streaming
    )
    
    claude = ClaudeAuthManager(config=config)
    
    response = await claude.query(
        "Explain machine learning in simple terms"
    )
    
    print(f"Response: {response.content[:200]}...")
    print(f"Configuration used SDK: {config.use_sdk}")
    print(f"Timeout: {config.timeout_seconds}s")
    
    await claude.shutdown()


async def streaming_example():
    """Streaming response example."""
    print("\n🔄 Streaming Example")
    print("-" * 25)
    
    # Streaming callback
    async def on_stream_update(update):
        print(f"[{update.type}] {update.content[:50]}{'...' if len(update.content) > 50 else ''}")
    
    claude = ClaudeAuthManager()
    
    response = await claude.query(
        "Write a short Python function to check if a number is prime",
        stream_callback=on_stream_update
    )
    
    print(f"\nFinal response received: {len(response.content)} characters")
    
    await claude.shutdown()


async def error_handling_example():
    """Error handling example."""
    print("\n⚠️ Error Handling Example")
    print("-" * 32)
    
    from claude_cli_auth.exceptions import ClaudeAuthError, ClaudeTimeoutError
    
    claude = ClaudeAuthManager()
    
    try:
        # This might fail if not authenticated
        response = await claude.query("Test query")
        print("✅ Query successful!")
        
    except ClaudeAuthError as e:
        print(f"❌ Authentication error: {e}")
        if hasattr(e, 'suggestions'):
            print("Suggestions:")
            for suggestion in e.suggestions:
                print(f"  • {suggestion}")
    
    except ClaudeTimeoutError as e:
        print(f"⏰ Timeout error: {e}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    await claude.shutdown()


async def main():
    """Run all examples."""
    print("🔐 Claude CLI Authentication Examples")
    print("=" * 45)
    
    try:
        await basic_query_example()
        await session_management_example()
        await file_context_example()
        await custom_config_example()
        await streaming_example()
        await error_handling_example()
        
        print("\n✅ All examples completed!")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("\nMake sure you have authenticated with Claude CLI:")
        print("  npm install -g @anthropic-ai/claude-code")
        print("  claude auth login")


if __name__ == "__main__":
    asyncio.run(main())