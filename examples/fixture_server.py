"""Safe local MCP fixture used by tests and the quick-start demo."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("MCP Conformance Fixture", instructions="A deterministic non-destructive test server.")


@mcp.tool()
def echo(text: str) -> str:
    """Return the supplied text without side effects."""
    return text


@mcp.resource("fixture://status", name="status", description="Static fixture status", mime_type="text/plain")
def status() -> str:
    """Return deterministic fixture status."""
    return "fixture-ok"


@mcp.prompt()
def greet(name: str) -> str:
    """Create a deterministic greeting prompt."""
    return f"Greet {name} politely."


if __name__ == "__main__":
    mcp.run(transport="stdio")
