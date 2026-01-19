"""DroidSession - core class for managing a single Droid session."""

from __future__ import annotations

import asyncio
import os
import subprocess
from dataclasses import dataclass, field
from typing import AsyncIterator

from .events import AgentMessage, Event
from .exceptions import SessionError, SessionNotAliveError
from .protocol import (
    JsonRpcNotification,
    add_user_message_request,
    interrupt_session_request,
    parse_message,
)
from .transport import FIFOTransport, resume_daemon, start_daemon


@dataclass
class DroidSession:
    """A single Droid CLI session."""

    name: str
    model: str
    pr_number: str
    cwd: str = field(default_factory=os.getcwd)
    session_id: str | None = None
    transport: FIFOTransport | None = None
    _process: subprocess.Popen | None = None

    async def start(self) -> str:
        """Start a new session and return the session ID."""
        self._process, self.transport = start_daemon(
            name=self.name,
            model=self.model,
            pr_number=self.pr_number,
            cwd=self.cwd,
        )

        self.session_id = await self.transport.wait_for_session_id()
        if not self.session_id:
            raise SessionError(f"Failed to get session ID for {self.name}")

        return self.session_id

    async def resume(self, session_id: str) -> None:
        """Resume an existing session."""
        self.session_id = session_id

        self._process, self.transport = resume_daemon(
            name=self.name,
            session_id=self.session_id,
            pr_number=self.pr_number,
            cwd=self.cwd,
        )

        await asyncio.sleep(2)

    async def send(self, text: str) -> None:
        """Send a message to the session."""
        if not self.transport:
            raise SessionNotAliveError(f"Session {self.name} not started")

        request = add_user_message_request(text)
        await self.transport.send_async(request)

    async def send_to(self, target: str, content: str) -> None:
        """Send a message to another agent."""
        msg = AgentMessage(
            from_agent=self.name,
            to_agent=target,
            content=content,
        )
        await self.send(msg.format())

    async def interrupt(self) -> None:
        """Interrupt the current operation."""
        if not self.transport:
            return

        request = interrupt_session_request()
        await self.transport.send_async(request)

    def is_alive(self) -> bool:
        """Check if the session is still running."""
        return self.transport is not None and self.transport.is_alive()

    async def stream_events(self) -> AsyncIterator[Event]:
        """Stream events from the session log."""
        if not self.transport:
            raise SessionNotAliveError(f"Session {self.name} not started")

        async for line in self.transport.read_log_lines():
            msg = parse_message(line)
            if isinstance(msg, JsonRpcNotification):
                if msg.method == "droid.session_notification":
                    notification = msg.params.get("notification", {})
                    yield Event.from_notification(notification)

    def cleanup(self) -> None:
        """Clean up session resources."""
        if self.transport:
            self.transport.cleanup()

    async def __aenter__(self) -> DroidSession:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()
