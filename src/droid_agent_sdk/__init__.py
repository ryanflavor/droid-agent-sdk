"""Droid Agent SDK - Communication layer for Factory Droid CLI.

Example:
    from droid_agent_sdk import DroidSession

    async with DroidSession(name="agent", model="claude-opus-4-5-20251101", pr_number="123") as session:
        await session.send("Hello!")
"""

from .events import AgentMessage, Event, EventType
from .exceptions import (
    DroidSDKError,
    FIFOError,
    ProtocolError,
    SessionError,
    SessionNotAliveError,
    SessionNotFoundError,
    TransportError,
)
from .protocol import (
    JsonRpcNotification,
    JsonRpcRequest,
    JsonRpcResponse,
    # Session lifecycle
    initialize_session_request,
    load_session_request,
    interrupt_session_request,
    update_session_settings_request,
    # Messages
    add_user_message_request,
    # Permissions
    request_permission_request,
    # MCP
    authenticate_mcp_server_request,
    retry_mcp_server_request,
    toggle_mcp_server_request,
    clear_mcp_auth_request,
)
from .session import DroidSession
from .swarm import Swarm
from .transport import FIFOTransport

__version__ = "0.2.0"

__all__ = [
    # Core classes
    "DroidSession",
    "Swarm",
    # Events
    "Event",
    "EventType",
    "AgentMessage",
    # Protocol
    "JsonRpcRequest",
    "JsonRpcResponse",
    "JsonRpcNotification",
    # Session lifecycle
    "initialize_session_request",
    "load_session_request",
    "interrupt_session_request",
    "update_session_settings_request",
    # Messages
    "add_user_message_request",
    # Permissions
    "request_permission_request",
    # MCP
    "authenticate_mcp_server_request",
    "retry_mcp_server_request",
    "toggle_mcp_server_request",
    "clear_mcp_auth_request",
    # Transport
    "FIFOTransport",
    # Exceptions
    "DroidSDKError",
    "SessionError",
    "SessionNotFoundError",
    "SessionNotAliveError",
    "TransportError",
    "FIFOError",
    "ProtocolError",
]
