"""JSON-RPC protocol implementation for Droid CLI.

Request methods (client → droid):
    - droid.initialize_session     初始化新 session
    - droid.load_session           恢复已有 session
    - droid.add_user_message       发送用户消息
    - droid.interrupt_session      中断当前执行
    - droid.update_session_settings 更新 session 设置
    - droid.request_permission     请求工具权限
    - droid.authenticate_mcp_server MCP 服务器认证
    - droid.retry_mcp_server       重试 MCP 服务器连接
    - droid.toggle_mcp_server      切换 MCP 服务器开关
    - droid.clear_mcp_auth         清除 MCP 认证

Notification methods (droid → client):
    - droid.session_notification   session 状态通知
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any


FACTORY_API_VERSION = "1.0.0"


@dataclass
class JsonRpcRequest:
    """JSON-RPC request message."""

    method: str
    params: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: f"req-{int(time.time() * 1000)}")

    def to_json(self) -> str:
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "type": "request",
                "factoryApiVersion": FACTORY_API_VERSION,
                "method": self.method,
                "params": self.params,
                "id": self.id,
            }
        )


@dataclass
class JsonRpcResponse:
    """JSON-RPC response message."""

    id: str
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None

    @property
    def is_error(self) -> bool:
        return self.error is not None

    @classmethod
    def from_json(cls, data: str | dict) -> JsonRpcResponse:
        if isinstance(data, str):
            data = json.loads(data)
        return cls(
            id=data.get("id", ""),
            result=data.get("result"),
            error=data.get("error"),
        )


@dataclass
class JsonRpcNotification:
    """JSON-RPC notification message."""

    method: str
    params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: str | dict) -> JsonRpcNotification:
        if isinstance(data, str):
            data = json.loads(data)
        return cls(
            method=data.get("method", ""),
            params=data.get("params", {}),
        )


def parse_message(line: str) -> JsonRpcResponse | JsonRpcNotification | None:
    """Parse a JSON-RPC message from a line."""
    try:
        data = json.loads(line)
        msg_type = data.get("type")
        if msg_type == "response":
            return JsonRpcResponse.from_json(data)
        elif msg_type == "notification":
            return JsonRpcNotification.from_json(data)
        return None
    except json.JSONDecodeError:
        return None


# =============================================================================
# Session lifecycle
# =============================================================================


def initialize_session_request(machine_id: str, cwd: str) -> JsonRpcRequest:
    """初始化新 session"""
    return JsonRpcRequest(
        method="droid.initialize_session",
        params={"machineId": machine_id, "cwd": cwd},
        id="init",
    )


def load_session_request(session_id: str) -> JsonRpcRequest:
    """恢复已有 session"""
    return JsonRpcRequest(
        method="droid.load_session",
        params={"sessionId": session_id},
        id="load",
    )


def interrupt_session_request() -> JsonRpcRequest:
    """中断当前执行"""
    return JsonRpcRequest(
        method="droid.interrupt_session",
        params={},
        id="interrupt",
    )


def update_session_settings_request(
    auto_mode: str | None = None,
    model: str | None = None,
) -> JsonRpcRequest:
    """更新 session 设置"""
    params = {}
    if auto_mode is not None:
        params["autoMode"] = auto_mode
    if model is not None:
        params["model"] = model
    return JsonRpcRequest(
        method="droid.update_session_settings",
        params=params,
        id="settings",
    )


# =============================================================================
# Messages
# =============================================================================


def add_user_message_request(text: str) -> JsonRpcRequest:
    """发送用户消息"""
    return JsonRpcRequest(
        method="droid.add_user_message",
        params={"text": text},
    )


# =============================================================================
# Permissions
# =============================================================================


def request_permission_request(
    tool_name: str,
    action: str = "allow",
    remember: bool = False,
) -> JsonRpcRequest:
    """请求工具权限

    Args:
        tool_name: Tool name to grant/deny permission
        action: "allow" or "deny"
        remember: Whether to remember this decision
    """
    return JsonRpcRequest(
        method="droid.request_permission",
        params={
            "toolName": tool_name,
            "action": action,
            "remember": remember,
        },
        id=f"perm-{tool_name}",
    )


# =============================================================================
# MCP (Model Context Protocol)
# =============================================================================


def authenticate_mcp_server_request(
    server_name: str,
    auth_token: str | None = None,
) -> JsonRpcRequest:
    """MCP 服务器认证"""
    params = {"serverName": server_name}
    if auth_token:
        params["authToken"] = auth_token
    return JsonRpcRequest(
        method="droid.authenticate_mcp_server",
        params=params,
        id=f"mcp-auth-{server_name}",
    )


def retry_mcp_server_request(server_name: str) -> JsonRpcRequest:
    """重试 MCP 服务器连接"""
    return JsonRpcRequest(
        method="droid.retry_mcp_server",
        params={"serverName": server_name},
        id=f"mcp-retry-{server_name}",
    )


def toggle_mcp_server_request(server_name: str, enabled: bool) -> JsonRpcRequest:
    """切换 MCP 服务器开关"""
    return JsonRpcRequest(
        method="droid.toggle_mcp_server",
        params={"serverName": server_name, "enabled": enabled},
        id=f"mcp-toggle-{server_name}",
    )


def clear_mcp_auth_request(server_name: str) -> JsonRpcRequest:
    """清除 MCP 认证"""
    return JsonRpcRequest(
        method="droid.clear_mcp_auth",
        params={"serverName": server_name},
        id=f"mcp-clear-{server_name}",
    )
