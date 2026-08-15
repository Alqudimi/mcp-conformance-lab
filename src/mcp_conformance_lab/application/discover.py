"""MCP discovery use case and contract mapping."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import Any, TypeVar

import anyio
from mcp import ClientSession
from mcp.types import (
    InitializeResult,
    ListPromptsResult,
    ListResourcesResult,
    ListResourceTemplatesResult,
    ListToolsResult,
)

from ..domain.errors import ProtocolError, TransportTimeoutError
from ..domain.models import (
    ContractSnapshot,
    PromptArgument,
    PromptContract,
    ResourceContract,
    ServerInfo,
    ToolContract,
)
from ..domain.policies import ExecutionPolicy

T = TypeVar("T")


async def _bounded(awaitable: Awaitable[T], timeout: float, operation: str) -> T:
    """Await one MCP operation with an explicit timeout."""
    try:
        with anyio.fail_after(timeout):
            return await awaitable
    except TimeoutError as exc:
        raise TransportTimeoutError(f"MCP operation timed out: {operation}") from exc


async def _list_tools(session: ClientSession, policy: ExecutionPolicy) -> list[Any]:
    """Collect all tool pages within the configured item bound."""
    items: list[Any] = []
    cursor: str | None = None
    while True:
        result: ListToolsResult = await _bounded(
            session.list_tools(cursor=cursor), policy.case_timeout_seconds, "tools/list"
        )
        items.extend(result.tools)
        if len(items) > policy.max_items:
            raise ProtocolError("tools/list exceeded the configured item limit")
        cursor = result.nextCursor
        if cursor is None:
            return items


async def _list_resources(session: ClientSession, policy: ExecutionPolicy) -> list[Any]:
    """Collect all resource pages within the configured item bound."""
    items: list[Any] = []
    cursor: str | None = None
    while True:
        result: ListResourcesResult = await _bounded(
            session.list_resources(cursor=cursor), policy.case_timeout_seconds, "resources/list"
        )
        items.extend(result.resources)
        if len(items) > policy.max_items:
            raise ProtocolError("resources/list exceeded the configured item limit")
        cursor = result.nextCursor
        if cursor is None:
            return items


async def _list_resource_templates(session: ClientSession, policy: ExecutionPolicy) -> list[Any]:
    """Collect all resource-template pages within the configured item bound."""
    items: list[Any] = []
    cursor: str | None = None
    while True:
        result: ListResourceTemplatesResult = await _bounded(
            session.list_resource_templates(cursor=cursor),
            policy.case_timeout_seconds,
            "resources/templates/list",
        )
        items.extend(result.resourceTemplates)
        if len(items) > policy.max_items:
            raise ProtocolError("resources/templates/list exceeded the configured item limit")
        cursor = result.nextCursor
        if cursor is None:
            return items


async def _list_prompts(session: ClientSession, policy: ExecutionPolicy) -> list[Any]:
    """Collect all prompt pages within the configured item bound."""
    items: list[Any] = []
    cursor: str | None = None
    while True:
        result: ListPromptsResult = await _bounded(
            session.list_prompts(cursor=cursor), policy.case_timeout_seconds, "prompts/list"
        )
        items.extend(result.prompts)
        if len(items) > policy.max_items:
            raise ProtocolError("prompts/list exceeded the configured item limit")
        cursor = result.nextCursor
        if cursor is None:
            return items


def _server_info(value: Any) -> ServerInfo:
    """Map SDK implementation metadata to the domain model."""
    return ServerInfo(
        name=getattr(value, "name", None),
        version=getattr(value, "version", None),
        title=getattr(value, "title", None),
    )


def _tool_contract(tool: Any) -> ToolContract:
    """Map one SDK tool into a strict contract model."""
    annotations = getattr(tool, "annotations", None)
    return ToolContract(
        name=tool.name,
        description=tool.description,
        input_schema=dict(tool.inputSchema),
        output_schema=dict(tool.outputSchema) if tool.outputSchema else None,
        annotations=annotations.model_dump(mode="json", exclude_none=True) if annotations else {},
    )


def _resource_contract(resource: Any) -> ResourceContract:
    """Map one SDK resource into a strict contract model."""
    return ResourceContract(
        uri=str(resource.uri),
        name=resource.name,
        description=resource.description,
        mime_type=resource.mimeType,
    )


def _prompt_contract(prompt: Any) -> PromptContract:
    """Map one SDK prompt into a strict contract model."""
    arguments = tuple(
        PromptArgument(
            name=argument.name,
            description=argument.description,
            required=bool(argument.required),
        )
        for argument in (prompt.arguments or [])
    )
    return PromptContract(name=prompt.name, description=prompt.description, arguments=arguments)


async def discover_session(session: ClientSession, policy: ExecutionPolicy) -> ContractSnapshot:
    """Initialize an MCP session and build a deterministic contract snapshot."""
    initialized: InitializeResult = await _bounded(
        session.initialize(), policy.connect_timeout_seconds, "initialize"
    )
    capabilities = initialized.capabilities.model_dump(mode="json", exclude_none=True)
    tools = (
        await _list_tools(session, policy)
        if getattr(initialized.capabilities, "tools", None)
        else []
    )
    resources = (
        await _list_resources(session, policy)
        if getattr(initialized.capabilities, "resources", None)
        else []
    )
    if getattr(initialized.capabilities, "resources", None):
        await _list_resource_templates(session, policy)
    prompts = (
        await _list_prompts(session, policy)
        if getattr(initialized.capabilities, "prompts", None)
        else []
    )
    return ContractSnapshot(
        protocol_version=str(initialized.protocolVersion),
        server_info=_server_info(initialized.serverInfo),
        capabilities=capabilities,
        tools=tuple(_tool_contract(tool) for tool in tools),
        resources=tuple(_resource_contract(resource) for resource in resources),
        prompts=tuple(_prompt_contract(prompt) for prompt in prompts),
    )
