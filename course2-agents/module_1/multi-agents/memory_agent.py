



# ================================
# 2. MemoryAgent：简单记忆存储
# ================================

from mcp.server.fastmcp import FastMCP
from state import MEMORY


def write_memory(key: str, value: str) -> str:
    """
    供其他 Agent 直接调用的普通函数。
    """
    MEMORY[key] = value
    return f"memory saved for key={key!r}"


def read_memory(key: str) -> str:
    return MEMORY.get(key, f"[no memory for key={key!r}]")


def list_memory_keys() -> list[str]:
    return list(MEMORY.keys())


def dump_memory() -> dict[str, str]:
    """调试用：查看当前所有记忆"""
    return dict(MEMORY)


def register_memory_tools(mcp: FastMCP) -> None:
    """
    注册 MemoryAgent 相关工具。
    """

    @mcp.tool()
    def write_memory_tool(key: str, value: str) -> str:
        return write_memory(key, value)

    @mcp.tool()
    def read_memory_tool(key: str) -> str:
        return read_memory(key)

    @mcp.tool()
    def list_memory_keys_tool() -> list[str]:
        return list_memory_keys()

    @mcp.tool()
    def dump_memory_tool() -> dict[str, str]:
        """调试用：查看当前所有记忆"""
        return dump_memory()
