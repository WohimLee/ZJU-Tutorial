from mcp.server.fastmcp import FastMCP

# 创建 MCP 应用
mcp = FastMCP("my-mcp")

# 定义一个最简单的工具
@mcp.tool()
def hello(name: str) -> str:
    return f"Hello, {name}! This is MCP."

# 启动服务器（stdio）
if __name__ == "__main__":
    mcp.run()
