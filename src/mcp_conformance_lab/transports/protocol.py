"""Transport-independent session protocol."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from mcp.types import (
    CallToolResult,
    GetPromptResult,
    InitializeResult,
    ListPromptsResult,
    ListResourcesResult,
    ListResourceTemplatesResult,
    ListToolsResult,
    ReadResourceResult,
)


class SessionAdapter(Protocol):
    """Minimal MCP session surface required by discovery and rules."""

    async def __aenter__(self) -> SessionAdapter:
        """Open the transport session."""
        ...

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        """Close the transport session."""
        ...

    async def initialize(self) -> InitializeResult:
        """Perform MCP initialization."""
        ...

    async def list_tools(self) -> ListToolsResult:
        """List available tools."""
        ...

    async def list_resources(self) -> ListResourcesResult:
        """List available resources."""
        ...

    async def list_resource_templates(self) -> ListResourceTemplatesResult:
        """List resource templates."""
        ...

    async def list_prompts(self) -> ListPromptsResult:
        """List available prompts."""
        ...

    async def call_tool(self, name: str, arguments: dict[str, object]) -> CallToolResult:
        """Call one tool through an explicit rule."""
        ...

    async def read_resource(self, uri: str) -> ReadResourceResult:
        """Read one resource through an explicit rule."""
        ...

    async def get_prompt(self, name: str, arguments: dict[str, str]) -> GetPromptResult:
        """Render one prompt through an explicit rule."""
        ...


class AdapterFactory(Protocol):
    """Factory protocol for application-level transport selection."""

    def __call__(self) -> AsyncIterator[SessionAdapter]:
        """Return an async context manager compatible iterator."""
        ...
