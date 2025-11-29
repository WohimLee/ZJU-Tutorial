
# ================================
# 3. LLMAgent：调用免费 DeepSeek API
# ================================


import os
import requests
from openai import OpenAI
from mcp.server.fastmcp import FastMCP
from state import CHORE_LOG

# 你可以用任意兼容 OpenAI 的免费端点
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
API_KEY = "sk-9f53ec0ec3234971af8af2c605c83c09"
MODEL_NAME = "qwen3-max"


def call_llm(prompt: str) -> str:
    """
    调用兼容 OpenAI 的 Chat Completions API，返回完整字符串结果。
    你可以把 BASE_URL + MODEL_NAME 换成任意免费的 LLM 服务。
    """
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=BASE_URL,
    )
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    # 这里不使用流式，直接取完整内容
    return completion.choices[0].message.content or ""


def summarize_chores_text() -> str:
    """
    非流式版本：将当前所有家务总结成一段完整文本。
    供 ManagerAgent 直接调用。
    """
    if not CHORE_LOG:
        return "今天没有记录任何家务。可以先用 log_chore(text=...) 添加。"

    text = "\n".join(f"- {c}" for c in CHORE_LOG)
    prompt = f"请把以下家务内容总结成一段自然语言：\n{text}"
    return call_llm(prompt)


def register_llm_tools(mcp: FastMCP) -> None:
    """
    注册与 LLM 相关的工具。
    """

    @mcp.tool()
    def summarize_chores() -> str:
        """
        用大模型把当前所有家务汇总成一段自然语言。
        """
        return summarize_chores_text()
