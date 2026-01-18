# Droid Agent SDK

Communication layer for Factory Droid CLI. Pure Python, zero dependencies.

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from droid_agent_sdk import DroidSession
import asyncio

async def main():
    async with DroidSession(
        name="agent",
        model="claude-opus-4-5-20251101",
        pr_number="123",
    ) as session:
        await session.send("Hello, review this PR...")

asyncio.run(main())
```

## JSON-RPC Protocol

SDK wraps the Droid CLI's stream-jsonrpc interface:

### Session Lifecycle

| Method | Function | Description |
|--------|----------|-------------|
| `droid.initialize_session` | `initialize_session_request()` | Create new session |
| `droid.load_session` | `load_session_request()` | Resume existing session |
| `droid.interrupt_session` | `interrupt_session_request()` | Interrupt current execution |
| `droid.update_session_settings` | `update_session_settings_request()` | Update session settings |

### Messages

| Method | Function | Description |
|--------|----------|-------------|
| `droid.add_user_message` | `add_user_message_request()` | Send user message |

### Permissions

| Method | Function | Description |
|--------|----------|-------------|
| `droid.request_permission` | `request_permission_request()` | Grant/deny tool permission |

### MCP (Model Context Protocol)

| Method | Function | Description |
|--------|----------|-------------|
| `droid.authenticate_mcp_server` | `authenticate_mcp_server_request()` | MCP server auth |
| `droid.retry_mcp_server` | `retry_mcp_server_request()` | Retry MCP connection |
| `droid.toggle_mcp_server` | `toggle_mcp_server_request()` | Enable/disable MCP server |
| `droid.clear_mcp_auth` | `clear_mcp_auth_request()` | Clear MCP auth |

### Notification Types

Droid sends `droid.session_notification` with these types:

| Type | Description |
|------|-------------|
| `droid_working_state_changed` | State: idle/streaming_assistant_message |
| `create_message` | New message created |
| `session_title_updated` | Session title changed |
| `thinking_text_delta` | Streaming thinking content |
| `assistant_text_delta` | Streaming response content |
| `mcp_status_changed` | MCP server status changed |

## Architecture

```
droid-agent-sdk/
├── protocol.py      # JSON-RPC message construction
├── transport.py     # FIFO communication
├── daemon_start.py  # Daemon for new session (initialize_session)
├── daemon_resume.py # Daemon for resume (load_session)
├── session.py       # DroidSession class
├── swarm.py         # Multi-session management (in memory)
└── events.py        # Event types
```

## Usage Examples

### Low-level Protocol

```python
from droid_agent_sdk import (
    initialize_session_request,
    add_user_message_request,
    interrupt_session_request,
)

# Build JSON-RPC requests
req = initialize_session_request(machine_id="myhost", cwd="/path")
print(req.to_json())
```

### Session Management

```python
from droid_agent_sdk import DroidSession

session = DroidSession(name="opus", model="claude-opus-4-5-20251101", pr_number="123")
session_id = await session.start()

await session.send("Review this code...")
await session.interrupt()

session.cleanup()
```

### Multi-Session (Swarm)

```python
from droid_agent_sdk import Swarm

async with Swarm(pr_number="123") as swarm:
    opus = await swarm.spawn("opus", model="claude-opus-4-5-20251101")
    codex = await swarm.spawn("codex", model="gpt-5.2")
    
    await swarm.send_to("opus", "codex", "Please review...")
```

## License

MIT
