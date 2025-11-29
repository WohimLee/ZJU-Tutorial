

# ================================
# 1. ActivityAgent：记录家务
# ================================

from mcp.server.fastmcp import FastMCP
from state import CHORE_LOG

def register_activity_tools(mcp: FastMCP) -> None:
    """
    在传入的 FastMCP 实例上注册 ActivityAgent 相关的工具。
    """

    @mcp.tool()
    def log_chore(text: str) -> str:
        """
        记录一条家务，例如：
            - "洗了碗"
            - "拖了地"
        """
        CHORE_LOG.append(text)
        return f"added chore: {text}"

    @mcp.tool()
    def list_chores() -> list[str]:
        """查看所有家务记录"""
        return list(CHORE_LOG)
