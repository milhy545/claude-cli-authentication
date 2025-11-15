# Claude CLI Authentication Module

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-claude--cli--auth-blue)](https://pypi.org/project/claude-cli-auth/)

A production-ready Python module for **Claude AI integration without API keys**. Uses Claude CLI authentication to work seamlessly with Claude subscriptions.

## 🎯 Key Features

- **🔑 No API Keys Required** - Uses `claude auth login` authentication
- **💳 Subscription Compatible** - Works with Claude subscription instead of API access
- **🌐 OpenAI-Compatible API Proxy** - Expose your subscription as an OpenAI-compatible REST API
- **🔄 Triple Fallback System** - SDK → CLI → Graceful error handling
- **💾 Session Management** - Persistent conversations and context
- **⚡ Production Ready** - Comprehensive error handling and logging
- **🎛️ Simple Interface** - Easy integration into any Python project

## 🚀 Quick Start

### Installation

```bash
# Install the module
pip install claude-cli-auth

# Install Claude CLI (required)
npm install -g @anthropic-ai/claude-code

# Authenticate with Claude (one-time setup)
claude auth login
```

### Basic Usage

```python
from claude_cli_auth import ClaudeAuthManager
from pathlib import Path

# Initialize the manager
claude = ClaudeAuthManager()

# Simple query
response = await claude.query(
    "Explain this code briefly",
    working_directory=Path(".")
)

print(response.content)
print(f"Cost: ${response.cost:.4f}")
```

### With Session Management

```python
# Start a conversation
response = await claude.query(
    "Create a Python function to calculate fibonacci numbers",
    session_id="my-coding-session"
)

# Continue the conversation
response = await claude.query(
    "Now add error handling and docstring to that function",
    session_id="my-coding-session",
    continue_session=True
)

print(response.content)
```

## 📚 Complete Documentation

### Configuration

```python
from claude_cli_auth import AuthConfig, ClaudeAuthManager

# Custom configuration
config = AuthConfig(
    timeout_seconds=60,           # Query timeout
    session_timeout_hours=24,     # Session expiration
    use_sdk=True,                # Prefer SDK over CLI
    enable_streaming=True,        # Enable streaming responses
)

claude = ClaudeAuthManager(config=config)
```

### Error Handling

```python
from claude_cli_auth import (
    ClaudeAuthError,
    ClaudeTimeoutError,
    ClaudeSessionError
)

try:
    response = await claude.query("Test query")
    print(response.content)
    
except ClaudeAuthError as e:
    print(f"Authentication issue: {e}")
    # Run: claude auth login
    
except ClaudeTimeoutError as e:
    print(f"Query timed out: {e}")
    # Retry with longer timeout
    
except ClaudeSessionError as e:
    print(f"Session problem: {e}")
    # Create new session
```

### Advanced Features

```python
# Streaming responses
async def on_stream_update(update):
    print(f"[{update.type}] {update.content}")

response = await claude.query(
    "Write a complex Python script",
    stream_callback=on_stream_update
)

# File context
response = await claude.query(
    "Review this code and suggest improvements",
    files=["app.py", "models.py"],
    working_directory=Path("./src")
)

# Session management
sessions = claude.list_sessions()
session_info = claude.get_session("my-session")

if session_info:
    print(f"Total cost: ${session_info.total_cost:.4f}")
    print(f"Messages: {session_info.total_turns}")
```

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│           Your Application          │
├─────────────────────────────────────┤
│        ClaudeAuthManager            │
│         (Main Interface)            │
├─────────────────────────────────────┤
│  Primary: Python SDK + CLI Auth    │
│  Fallback: Direct CLI Subprocess   │
│  Emergency: Error Recovery          │
├─────────────────────────────────────┤
│        Claude CLI (~/.claude/)     │
└─────────────────────────────────────┘
```

## 🔧 Core Components

- **`AuthManager`** - Session and credential management
- **`CLIInterface`** - Direct CLI subprocess wrapper  
- **`SDKInterface`** - Python SDK with CLI authentication (optional)
- **`ClaudeAuthManager`** - Unified API with intelligent fallbacks

## ⚙️ Requirements

- **Python 3.8+**
- **Claude CLI** - Install with `npm install -g @anthropic-ai/claude-code`
- **Claude Authentication** - Run `claude auth login` (one-time setup)

## 🚨 Troubleshooting

### Common Issues

**"Claude CLI not authenticated"**
```bash
claude auth login
```

**"Claude CLI not found"**  
```bash
npm install -g @anthropic-ai/claude-code
```

**"Session expired"**
```python
# Sessions auto-expire after 24 hours
await claude.cleanup_sessions()
```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging
claude = ClaudeAuthManager()
```

## 📖 Integration Examples

### Flask/FastAPI Integration

```python
from flask import Flask, request, jsonify
from claude_cli_auth import ClaudeAuthManager

app = Flask(__name__)
claude = ClaudeAuthManager()

@app.route('/ask', methods=['POST'])
async def ask_claude():
    data = request.json
    
    try:
        response = await claude.query(
            prompt=data['question'],
            session_id=data.get('session_id')
        )
        
        return jsonify({
            'response': response.content,
            'session_id': response.session_id,
            'cost': response.cost
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Telegram Bot Integration

```python
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from claude_cli_auth import ClaudeAuthManager

claude = ClaudeAuthManager()

async def handle_message(update: Update, context):
    user_id = update.effective_user.id
    
    response = await claude.query(
        prompt=update.message.text,
        session_id=f"telegram_{user_id}"
    )
    
    await update.message.reply_text(response.content)
```

### Jupyter Notebook Integration

```python
from claude_cli_auth import ClaudeAuthManager
import asyncio

# Initialize in notebook
claude = ClaudeAuthManager()

# Use in any cell
async def ask_claude(question):
    response = await claude.query(question)
    return response.content

# Example usage
result = await ask_claude("Explain machine learning in simple terms")
print(result)
```

## 🌐 OpenAI-Compatible API Proxy

**NEW!** Use your Claude subscription as an OpenAI-compatible REST API!

### Why Use the API Proxy?

- ✅ Use subscription pricing instead of expensive API rates
- ✅ Compatible with OpenAI client libraries and tools
- ✅ Enable remote access to Claude Code
- ✅ Integrate with LangChain, AutoGPT, and other frameworks

### Quick Start

```bash
# Start the proxy server
claude-api-proxy --port 8000

# Use with any OpenAI-compatible client
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### With OpenAI Python Client

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy-key"  # Not validated
)

response = client.chat.completions.create(
    model="claude-sonnet-4",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

### With LangChain

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy-key",
    model="claude-sonnet-4"
)

response = llm.invoke("Explain quantum computing")
print(response.content)
```

**📖 Full documentation:** [API_PROXY.md](API_PROXY.md)

## 🔒 Security & Privacy

- **No API Keys Stored** - Uses secure Claude CLI authentication
- **Local Session Storage** - Sessions stored in `~/.claude/` directory
- **No Data Sent to Third Parties** - Direct communication with Claude
- **Audit Logging** - Comprehensive operation tracking available

## 🤝 Contributing

This module is designed to be a stable, focused authentication layer. Contributions welcome for:

- Bug fixes and reliability improvements
- Additional authentication methods
- Enhanced error handling
- Performance optimizations

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Pure Claude Authentication** - Simple, reliable, no API keys required! 🔐