"""Local Streamable HTTP fixture used for adapter smoke tests."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "MCP Conformance HTTP Fixture",
    instructions="A deterministic non-destructive HTTP test server.",
    host="127.0.0.1",
    port=8765,
)


@mcp.tool()
def echo(text: str) -> str:
    """Return the supplied text without side effects."""
    return text


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
