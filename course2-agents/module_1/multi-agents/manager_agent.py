
# ================================
# 4. ManagerAgent：一键完成 A2A + 记忆存储
# ================================

# manager_agent.py
from mcp.server.fastmcp import FastMCP, Context

# 注意：这里我们导入的是函数本身，
# 实际上这些函数已经通过各自的 register_xxx_tools 作为 MCP 工具暴露出去。
from memory_agent import write_memory  # type: ignore
from llm_agent import summarize_chores_text  # type: ignore
from state import CHORE_LOG


def register_manager_tools(mcp: FastMCP) -> None:
    """
    注册 ManagerAgent 的组合工具，体现 A2A。
    """

    @mcp.tool()
    def summarize_and_remember(
        topic_key: str = "daily_chores",
        ctx: Context | None = None,
    ) -> str:
        """
        A2A 工作流：
            1. 读取家务（ActivityAgent 已记录到 CHORE_LOG）
            2. 用 LLM 总结（LLMAgent）
            3. 写入记忆（MemoryAgent）
        """
        if not CHORE_LOG:
            return "今天还没记录家务，可先用 log_chore(text=...) 添加。"

        # 2. 用 LLM 生成总结（LLMAgent）
        summary = summarize_chores_text()

        # 3. 写入记忆（MemoryAgent）
        write_memory(topic_key, summary)

        if ctx is not None:
            ctx.info(f"[ManagerAgent] saved summary under memory key={topic_key!r}")

        return (
            f"已为你生成今日家务总结，并写入记忆 key={topic_key!r}：\n\n"
            f"{summary}"
        )
