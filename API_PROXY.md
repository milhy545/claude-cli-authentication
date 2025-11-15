# Claude API Proxy 🚀

**OpenAI-compatible API using your Claude subscription instead of expensive API keys!**

The Claude API Proxy converts your Claude subscription into an OpenAI-compatible REST API, allowing you to use tools like Claude Code, LangChain, and other AI frameworks **without paying for API access**.

## 🎯 Why Use This?

| Scenario | Solution |
|----------|----------|
| ❌ You have Claude subscription but no API access | ✅ Use subscription via API proxy |
| ❌ API keys are too expensive for your use case | ✅ Use subscription pricing instead |
| ❌ Tools require OpenAI-compatible API | ✅ Proxy provides compatible interface |
| ❌ Want to control Claude Code remotely | ✅ API proxy enables remote access |

## 🚀 Quick Start

### 1. Install

```bash
pip install claude-cli-auth
```

### 2. Authenticate

```bash
# One-time authentication with Claude
claude auth login
```

### 3. Start the Proxy

```bash
# Start on localhost:8000
claude-api-proxy --port 8000

# Or bind to all interfaces for remote access
claude-api-proxy --host 0.0.0.0 --port 8000

# With custom timeout
claude-api-proxy --port 8000 --timeout 300
```

### 4. Use It!

```bash
# Test with curl
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'
```

## 📚 Usage Examples

### With OpenAI Python Client

```python
from openai import OpenAI

# Point to your proxy instead of OpenAI
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy-key"  # Not validated, but required by client
)

# Use exactly like OpenAI!
response = client.chat.completions.create(
    model="claude-sonnet-4",
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ]
)

print(response.choices[0].message.content)
```

### Streaming Responses

```python
# Streaming works too!
stream = client.chat.completions.create(
    model="claude-sonnet-4",
    messages=[
        {"role": "user", "content": "Write a Python function for fibonacci"}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### With LangChain

```python
from langchain_openai import ChatOpenAI

# Initialize LangChain with your proxy
llm = ChatOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy-key",
    model="claude-sonnet-4"
)

# Use as normal
response = llm.invoke("Explain machine learning")
print(response.content)

# Streaming
for chunk in llm.stream("Write a poem"):
    print(chunk.content, end="")
```

### With Claude Code

To use with Claude Code or other tools that expect Anthropic API:

```bash
# Set environment variables
export ANTHROPIC_API_URL=http://localhost:8000/v1
export ANTHROPIC_API_KEY=dummy-key

# Now use Claude Code as normal!
```

## 🔧 API Endpoints

### Chat Completions

**POST** `/v1/chat/completions`

OpenAI-compatible chat completions endpoint.

**Request:**
```json
{
  "model": "claude-sonnet-4",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false,
  "temperature": 1.0,
  "max_tokens": null,
  "user": "optional-user-id"
}
```

**Response (non-streaming):**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1699564800,
  "model": "claude-sonnet-4",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

**Response (streaming):**
```
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1699564800,"model":"claude-sonnet-4","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1699564800,"model":"claude-sonnet-4","choices":[{"index":0,"delta":{"content":"!"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1699564800,"model":"claude-sonnet-4","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

### List Models

**GET** `/v1/models`

List available models (OpenAI-compatible format).

**Response:**
```json
{
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
}
```

### Health Check

**GET** `/health`

Check proxy health and statistics.

**Response:**
```json
{
  "status": "healthy",
  "claude_authenticated": true,
  "stats": {
    "total_requests": 42,
    "streaming_requests": 15,
    "failed_requests": 2,
    "total_cost": 0.125
  },
  "active_requests": 0
}
```

## 🔒 Security Considerations

### Local Development
```bash
# Safe: Only accessible from your machine
claude-api-proxy --host 127.0.0.1 --port 8000
```

### Remote Access
```bash
# Warning: Accessible from anywhere!
# Only use on trusted networks or with additional security
claude-api-proxy --host 0.0.0.0 --port 8000
```

**Important Security Notes:**
- ⚠️ The proxy does **NOT** validate API keys (uses subscription auth)
- ⚠️ Binding to `0.0.0.0` exposes the proxy to your network
- ⚠️ Use firewall rules or VPN for remote access
- ✅ Consider running behind nginx with authentication
- ✅ Use SSH tunneling for secure remote access

### Secure Remote Access (SSH Tunnel)

```bash
# On remote server
claude-api-proxy --host 127.0.0.1 --port 8000

# On local machine
ssh -L 8000:localhost:8000 user@remote-server

# Now use http://localhost:8000 locally!
```

## 🎛️ Configuration

### Command-Line Options

```bash
claude-api-proxy \
  --host 0.0.0.0 \          # Host to bind to (default: 127.0.0.1)
  --port 8000 \             # Port to bind to (default: 8000)
  --timeout 300 \           # Query timeout in seconds (default: 120)
  --debug                   # Enable debug logging
```

### Environment Variables

The proxy respects Claude CLI configuration:

```bash
# Custom Claude CLI path
export CLAUDE_CLI_PATH=/custom/path/to/claude

# Custom config directory
export CLAUDE_CONFIG_DIR=~/.claude-custom
```

## 📊 Monitoring

### API Documentation

The proxy provides interactive API documentation:

```
http://localhost:8000/docs       # Swagger UI
http://localhost:8000/redoc      # ReDoc
```

### Health Monitoring

```bash
# Check health
curl http://localhost:8000/health

# Watch health in real-time
watch -n 1 'curl -s http://localhost:8000/health | jq'
```

### Logging

```bash
# Enable debug logging
claude-api-proxy --debug --port 8000

# Logs include:
# - Request/response details
# - Claude CLI execution
# - Streaming events
# - Error details
# - Performance metrics
```

## 🐛 Troubleshooting

### Proxy won't start

**Error:** `Claude CLI is not authenticated`
```bash
# Solution: Authenticate with Claude
claude auth login
```

**Error:** `Address already in use`
```bash
# Solution: Use different port
claude-api-proxy --port 8001
```

### Requests failing

**Error:** `503 Service Unavailable`
```bash
# Check health
curl http://localhost:8000/health

# Check Claude authentication
claude auth status
```

**Error:** Timeout errors
```bash
# Increase timeout
claude-api-proxy --timeout 300
```

### Streaming not working

**Issue:** Stream not showing real-time updates

Most likely cause: The Claude CLI doesn't support real-time streaming in all cases. The proxy will still work, but updates may come in larger chunks rather than token-by-token.

**Workaround:** Use non-streaming mode if real-time updates aren't critical.

## 🔬 Advanced Usage

### Programmatic Usage

```python
from claude_cli_auth.api_proxy import ClaudeAPIProxy
from claude_cli_auth import AuthConfig

# Custom configuration
config = AuthConfig(
    timeout_seconds=300,
    max_turns=20,
)

# Initialize proxy
proxy = ClaudeAPIProxy(
    config=config,
    host="127.0.0.1",
    port=8000
)

# Use programmatically
from claude_cli_auth.api_proxy import ChatCompletionRequest, ChatMessage

request = ChatCompletionRequest(
    model="claude-sonnet-4",
    messages=[ChatMessage(role="user", content="Hello!")]
)

response = await proxy.handle_chat_completion(request)
print(response.choices[0].message.content)

# Cleanup
await proxy.shutdown()
```

### Running as a Service

#### systemd (Linux)

Create `/etc/systemd/system/claude-api-proxy.service`:

```ini
[Unit]
Description=Claude API Proxy
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser
ExecStart=/usr/local/bin/claude-api-proxy --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable claude-api-proxy
sudo systemctl start claude-api-proxy

# Check status
sudo systemctl status claude-api-proxy
```

#### Docker

```dockerfile
FROM python:3.11-slim

# Install Node.js for Claude CLI
RUN apt-get update && apt-get install -y nodejs npm

# Install Claude CLI
RUN npm install -g @anthropic-ai/claude-code

# Install Python package
RUN pip install claude-cli-auth

# Authenticate (you'll need to handle this)
# COPY .claude /root/.claude

EXPOSE 8000

CMD ["claude-api-proxy", "--host", "0.0.0.0", "--port", "8000"]
```

## 💡 Use Cases

### 1. Remote Claude Code Access
Access Claude Code from anywhere using the API proxy:
```bash
# On server
claude-api-proxy --host 0.0.0.0 --port 8000

# From anywhere
export ANTHROPIC_API_URL=http://server:8000/v1
claude-code
```

### 2. Cost Savings
Use subscription pricing instead of API pricing:
- Claude Pro: ~$20/month unlimited
- Claude API: $3-15 per million tokens
- **Savings:** Potentially thousands of dollars for heavy users

### 3. Team Access
Share your subscription with your team (within terms of service):
```bash
# Central proxy server
claude-api-proxy --host 0.0.0.0 --port 8000

# Team members connect
export ANTHROPIC_API_URL=http://team-server:8000/v1
```

### 4. Integration Testing
Test AI integrations without API costs:
```python
# In tests
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="test"
)

# Test your code without API charges!
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built with** ❤️ **for developers who want to use Claude without breaking the bank!** 💰
