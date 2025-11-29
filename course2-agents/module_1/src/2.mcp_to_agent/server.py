
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Local Calculator", json_response=True)


@mcp.tool()
def add(a: int, b: int) -> int:
    """对两个整数求和，返回 a + b"""
    return a + b


@mcp.tool()
def sub(a: int, b: int) -> int:
    """对两个整数求差，返回 a - b"""
    return a - b


if __name__ == "__main__":
    # 用 stdio 模式跑一个 MCP server
    mcp.run(transport="stdio")
