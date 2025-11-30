
from mcp.server.fastmcp import FastMCP

# 创建 MCP server，返回 JSON 结构结果更方便给 LLM 用
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
    # 用 stdio 作为传输方式，方便被本地 client 作为子进程拉起来
    mcp.run(transport="stdio")
