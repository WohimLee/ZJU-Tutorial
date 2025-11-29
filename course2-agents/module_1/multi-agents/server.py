


# server.py
from mcp.server.fastmcp import FastMCP

from activity_agent import register_activity_tools
from memory_agent import register_memory_tools
from llm_agent import register_llm_tools
from manager_agent import register_manager_tools


def create_app() -> FastMCP:
    mcp = FastMCP("Home-Chores-MultiAgent")

    # 在同一个 MCP 实例上注册不同模块的工具
    register_activity_tools(mcp)
    register_memory_tools(mcp)
    register_llm_tools(mcp)
    register_manager_tools(mcp)

    return mcp

app = create_app()


if __name__ == "__main__":
    app.run()
