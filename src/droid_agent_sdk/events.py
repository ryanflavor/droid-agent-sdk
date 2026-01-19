"""Event types for Droid session notifications."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Types of events from Droid session."""

    # Session lifecycle
    SESSION_INITIALIZED = "session_initialized"
    SESSION_LOADED = "session_loaded"

    # Working state
    STATE_CHANGED = "droid_working_state_changed"

    # Messages
    MESSAGE_CREATED = "create_message"
    TITLE_UPDATED = "session_title_updated"

    # Streaming content
    THINKING_DELTA = "thinking_text_delta"
    TEXT_DELTA = "assistant_text_delta"

    # Tools
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"

    # MCP
    MCP_STATUS = "mcp_status_changed"

    # Completion
    COMPLETE = "complete"

    # Errors
    ERROR = "error"

    # Unknown
    UNKNOWN = "unknown"


@dataclass
class Event:
    """Base event from Droid session."""

    type: EventType
    data: dict[str, Any]

    @classmethod
    def from_notification(cls, notification: dict[str, Any]) -> Event:
        """Create an Event from a notification dict."""
        event_type_str = notification.get("type", "unknown")

        try:
            event_type = EventType(event_type_str)
        except ValueError:
            event_type = EventType.UNKNOWN

        return cls(type=event_type, data=notification)

    @property
    def message_id(self) -> str | None:
        return self.data.get("messageId")

    @property
    def text(self) -> str | None:
        """Get text content (for delta events)."""
        return self.data.get("textDelta") or self.data.get("text")

    @property
    def new_state(self) -> str | None:
        """Get new state (for state change events)."""
        return self.data.get("newState")


@dataclass
class TextDeltaEvent(Event):
    """Text streaming event."""

    @property
    def block_index(self) -> int:
        return self.data.get("blockIndex", 0)


@dataclass
class MessageEvent(Event):
    """Message created event."""

    @property
    def message(self) -> dict[str, Any]:
        return self.data.get("message", {})

    @property
    def role(self) -> str:
        return self.message.get("role", "")

    @property
    def content(self) -> list[dict[str, Any]]:
        return self.message.get("content", [])


@dataclass
class AgentMessage:
    """A message from one agent to another."""

    from_agent: str
    to_agent: str
    content: str
    timestamp: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "from": self.from_agent,
            "to": self.to_agent,
            "content": self.content,
            "timestamp": self.timestamp,
        }

    def format(self) -> str:
        """Format message for FIFO transport."""
        return f'<MESSAGE from="{self.from_agent}" to="{self.to_agent}">\n{self.content}\n</MESSAGE>'

    @classmethod
    def parse(cls, text: str) -> AgentMessage | None:
        """Parse a formatted agent message."""
        import re

        match = re.match(
            r'<MESSAGE from="(\w+)" to="(\w+)">\n(.*)\n</MESSAGE>', text, re.DOTALL
        )
        if match:
            return cls(
                from_agent=match.group(1),
                to_agent=match.group(2),
                content=match.group(3),
            )
        return None
