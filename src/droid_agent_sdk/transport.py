"""FIFO transport layer for Droid CLI communication."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator

from .exceptions import FIFOError
from .protocol import (
    JsonRpcRequest,
)


@dataclass
class FIFOTransport:
    """FIFO-based transport for communicating with a Droid session."""

    fifo_path: Path
    log_path: Path
    pid: int | None = None
    _process: subprocess.Popen | None = None

    @classmethod
    def create(cls, name: str, pr_number: str) -> FIFOTransport:
        """Create a new FIFO transport."""
        fifo_path = Path(f"/tmp/duo-{pr_number}-{name}")
        log_path = Path(f"/tmp/duo-{pr_number}-{name}.log")

        # Clean up old FIFO
        if fifo_path.exists():
            fifo_path.unlink()

        # Create new FIFO
        os.mkfifo(fifo_path)

        # Clear log
        log_path.write_text("")

        return cls(fifo_path=fifo_path, log_path=log_path)

    @classmethod
    def restore(
        cls, fifo_path: str, log_path: str, pid: int | None = None
    ) -> FIFOTransport:
        """Restore a FIFO transport from existing paths."""
        return cls(
            fifo_path=Path(fifo_path),
            log_path=Path(log_path),
            pid=pid,
        )

    def send(self, request: JsonRpcRequest) -> None:
        """Send a request through the FIFO (blocking)."""
        if not self.fifo_path.exists():
            raise FIFOError(f"FIFO not found: {self.fifo_path}")

        message = request.to_json() + "\n"
        with open(self.fifo_path, "w") as f:
            f.write(message)

    async def send_async(self, request: JsonRpcRequest) -> None:
        """Send a request through the FIFO (async)."""
        await asyncio.to_thread(self.send, request)

    def is_alive(self) -> bool:
        """Check if the daemon process is still running."""
        if self.pid is None:
            return False
        try:
            os.kill(self.pid, 0)
            # Verify it's a Python process (our daemon)
            result = subprocess.run(
                ["ps", "-p", str(self.pid), "-o", "comm="],
                capture_output=True,
                text=True,
            )
            return "python" in result.stdout.lower()
        except (OSError, ValueError):
            return False

    async def read_log_lines(self, start_pos: int = 0) -> AsyncIterator[str]:
        """Read new lines from the log file."""
        with open(self.log_path, "r") as f:
            f.seek(start_pos)
            while True:
                line = f.readline()
                if line:
                    yield line.strip()
                else:
                    await asyncio.sleep(0.1)

    async def wait_for_session_id(self, timeout: float = 10.0) -> str | None:
        """Wait for session ID to appear in the log."""
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                content = self.log_path.read_text()
                for line in content.split("\n"):
                    if '"sessionId"' in line:
                        data = json.loads(line)
                        if "result" in data and "sessionId" in data["result"]:
                            return data["result"]["sessionId"]
            except (json.JSONDecodeError, KeyError, FileNotFoundError):
                pass
            await asyncio.sleep(0.5)

        return None

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.pid and self.is_alive():
            try:
                os.kill(self.pid, 15)  # SIGTERM
            except OSError:
                pass

        if self.fifo_path.exists():
            try:
                self.fifo_path.unlink()
            except OSError:
                pass


def start_daemon(
    name: str,
    model: str,
    pr_number: str,
    cwd: str,
    auto_level: str = "high",
) -> tuple[subprocess.Popen, FIFOTransport]:
    """Start a new Droid session (initialize_session)."""
    transport = FIFOTransport.create(name, pr_number)

    daemon_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "droid_agent_sdk.daemon_start",
            name,
            model,
            pr_number,
            cwd,
            auto_level,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        env=os.environ.copy(),
    )

    transport.pid = daemon_proc.pid
    return daemon_proc, transport


def resume_daemon(
    name: str,
    session_id: str,
    pr_number: str,
    cwd: str,
    auto_level: str = "high",
) -> tuple[subprocess.Popen, FIFOTransport]:
    """Resume an existing Droid session (load_session)."""
    transport = FIFOTransport.create(name, pr_number)

    daemon_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "droid_agent_sdk.daemon_resume",
            name,
            pr_number,
            session_id,
            cwd,
            auto_level,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        env=os.environ.copy(),
    )

    transport.pid = daemon_proc.pid
    return daemon_proc, transport
