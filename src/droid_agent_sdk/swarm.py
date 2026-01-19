"""Swarm - manage multiple Droid sessions in memory."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Iterator

from .events import AgentMessage
from .exceptions import SessionNotFoundError
from .session import DroidSession


@dataclass
class Swarm:
    """Manage multiple Droid sessions (in memory only)."""

    pr_number: str
    repo: str = ""
    branch: str = ""
    base_branch: str = ""
    cwd: str = field(default_factory=os.getcwd)

    _sessions: dict[str, DroidSession] = field(default_factory=dict)

    async def spawn(
        self,
        name: str,
        model: str = "claude-opus-4-5-20251101",
    ) -> DroidSession:
        """Spawn a new agent session."""
        session = DroidSession(
            name=name,
            model=model,
            pr_number=self.pr_number,
            cwd=self.cwd,
        )

        await session.start()
        self._sessions[name] = session

        return session

    def get(self, name: str) -> DroidSession:
        """Get an existing session by name."""
        if name not in self._sessions:
            raise SessionNotFoundError(f"Session {name} not found in swarm")
        return self._sessions[name]

    async def send_to(self, from_agent: str, to_agent: str, message: str) -> None:
        """Send a message from one agent to another."""
        if to_agent not in self._sessions:
            raise SessionNotFoundError(f"Session {to_agent} not found")

        target = self._sessions[to_agent]
        msg = AgentMessage(from_agent=from_agent, to_agent=to_agent, content=message)
        await target.send(msg.format())

    @property
    def session_ids(self) -> dict[str, str | None]:
        """Get all session IDs."""
        return {name: s.session_id for name, s in self._sessions.items()}

    @property
    def agents(self) -> list[str]:
        """Get all agent names."""
        return list(self._sessions.keys())

    def __iter__(self) -> Iterator[DroidSession]:
        return iter(self._sessions.values())

    async def shutdown(self) -> None:
        """Shutdown all sessions."""
        for session in self._sessions.values():
            session.cleanup()
        self._sessions.clear()

    async def __aenter__(self) -> Swarm:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.shutdown()
