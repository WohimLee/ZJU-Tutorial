import os
import sys
import json
import asyncio
from typing import Dict, Any, List

from openai import OpenAI

from mcp import ClientSession, StdioServerParameters, types as mcp_types
from mcp.client.stdio import stdio_client

from dotenv import load_dotenv
load_dotenv("/Users/azen/Desktop/llm/ZJU-Tutorial/.env")

############################################
# 1. 初始化 LLM 客户端
############################################

llm_client = OpenAI(
    # 若没有配置环境变量，请改成：
    # api_key="sk-xxx",
    # base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("ALIBABA_API_KEY"),
    base_url=os.getenv("ALIBABA_API_URL"),
)

MODEL_NAME = "qwen3-max"

############################################
# 2. System 提示词（基础角色设定）
############################################

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "你是一个会主动使用工具的智能助手。"
        "当你需要查询实时信息、天气等时，请优先调用提供的工具。"
        "你可以多次调用工具，直到拿到足够信息后，再给出中文回答。"
    ),
}

############################################
# 3. 基于 MCP 的工具发现 & 转换
############################################


async def get_oai_tools_from_mcp(session: ClientSession) -> List[Dict[str, Any]]:
    """
    从 MCP server 获取工具列表，并转换成 OpenAI Chat Completions 所需的 tools schema。
    """
    tools_result = await session.list_tools()
    mcp_tools = [tool.model_dump() for tool in tools_result.tools]

    oai_tools: List[Dict[str, Any]] = []
    for t in mcp_tools:
        # FastMCP 的 Tool 对象中，schema 字段名一般为 inputSchema
        input_schema = t.get("inputSchema") or {}

        oai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    # MCP 的 inputSchema 与 OpenAI 的 parameters 字段语义一致
                    "parameters": input_schema,
                },
            }
        )

    return oai_tools


async def call_mcp_tool(
    session: ClientSession, tool_name: str, tool_args: Dict[str, Any]
) -> str:
    """
    调用 MCP tool，并把返回的内容拼成一个字符串给 LLM history 使用。
    """
    result = await session.call_tool(name=tool_name, arguments=tool_args)

    # MCP 返回的是一组 content block，我们只需要把 text 拼起来即可
    parts: List[str] = []
    for item in result.content:
        # TextContent 类型有 text 属性
        text = getattr(item, "text", None)
        if text is not None:
            parts.append(text)
        else:
            parts.append(str(item))

    return "\n".join(parts)


############################################
# 4. LLM 调用（使用 MCP tools）
############################################


def call_llm_with_tools(
    history: List[Dict[str, Any]], tools: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    调一次 LLM，让它决定是否调用工具（tool_choice='auto'）。
    返回的是 message 对象（dict）—— ChatCompletionMessage。
    """
    response = llm_client.chat.completions.create(
        model=MODEL_NAME,
        messages=history,
        tools=tools,
        tool_choice="auto",
        stream=False,
    )
    return response.choices[0].message


def final_summarize(history: List[Dict[str, Any]]) -> str:
    """
    使用流式输出的方式，在终端实时打印大模型最终回复。
    注意这里 tool_choice='none'，不再允许调用工具。
    """
    print("助手：", end="", flush=True)

    stream = llm_client.chat.completions.create(
        model=MODEL_NAME,
        messages=history,
        stream=True,
        tool_choice="none",  # 最终阶段禁止工具调用
    )

    full_content = ""
    for chunk in stream:
        delta = chunk.choices[0].delta
        content = getattr(delta, "content", None) or ""
        if content:
            print(content, end="", flush=True)
            full_content += content
    print()  # 换行
    return full_content


async def run_agent_once(
    user_input: str,
    history: List[Dict[str, Any]],
    mcp_session: ClientSession,
    oai_tools: List[Dict[str, Any]],
    max_tool_rounds: int = 5,
) -> str:
    """
    针对一次用户输入，执行一个完整的 agent 流程（基于 MCP 工具）：
    - 多轮工具调用（最多 max_tool_rounds 轮）
    - 最后使用 stream=True 做自然语言总结
    返回最终完整回复字符串。
    """

    # 先把用户输入 push 到 history
    history.append({"role": "user", "content": user_input})

    # 多轮工具调用循环
    for _ in range(max_tool_rounds):
        msg = call_llm_with_tools(history, tools=oai_tools)

        # 先把本轮 assistant 消息加进历史（包括可能的 tool_calls）
        assistant_msg: Dict[str, Any] = {
            "role": "assistant",
            "content": msg.content,
        }
        if msg.tool_calls:
            assistant_msg["tool_calls"] = msg.tool_calls
        history.append(assistant_msg)

        # 如果没有 tool_calls，说明模型觉得自己已经可以直接回答
        if not msg.tool_calls:
            break

        # 否则，通过 MCP 调用每个工具
        for tool_call in msg.tool_calls:
            tool_name = tool_call.function.name
            raw_args = tool_call.function.arguments or "{}"

            try:
                if isinstance(raw_args, str):
                    tool_args = json.loads(raw_args)
                else:
                    tool_args = raw_args
            except json.JSONDecodeError:
                tool_args = {}

            print("模型要求调用函数：", tool_name, "参数：", tool_args)

            try:
                tool_result = await call_mcp_tool(
                    session=mcp_session, tool_name=tool_name, tool_args=tool_args
                )
            except Exception as e:
                tool_result = f"[调用 MCP 工具 {tool_name} 出错: {e!r}]"

            # 把工具结果作为 role=tool 消息塞回去
            history.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": str(tool_result),
                }
            )

        # 然后进入下一轮循环，看模型要不要再次发起 tool_calls

    # 工具阶段结束后，做一次“最终回答”，禁止继续调用工具
    final_answer = final_summarize(history)
    # 把最终自然语言回答也加入历史（方便多轮对话）
    history.append({"role": "assistant", "content": final_answer})
    return final_answer


############################################
# 5. 历史裁剪 & 主入口
############################################


def truncate_history(
    history: List[Dict[str, Any]], max_messages: int = 30
) -> List[Dict[str, Any]]:
    """
    简单的历史裁剪：只保留最近 max_messages 条消息（外加 system）。
    防止长时间对话导致上下文太长。
    """
    msgs = [m for m in history if m["role"] != "system"]
    if len(msgs) <= max_messages:
        return history

    # 保留 system + 最近 N 条非 system 消息
    new_history = [SYSTEM_MESSAGE] + msgs[-max_messages:]
    return new_history


async def chat_loop():
    """
    启动 MCP server 子进程（通过 stdio），并进行多轮对话。
    """
    # 配置通过 stdio 连接到本地的 server.py
    server_params = StdioServerParameters(
        command=sys.executable,  # 当前 Python 解释器
        args=[
            "server.py",  # 确保与 server 文件名一致
        ],
    )

    # 对话级别的 history（包含 system）
    history: List[Dict[str, Any]] = [SYSTEM_MESSAGE]

    print("已启动 MCP 工具增强 Agent，对话中输入 exit / 退出 即可结束。")

    # 启动 MCP 客户端（子进程方式）
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            # 初始化 MCP 会话
            await mcp_session.initialize()

            # 从 MCP 动态获取工具，并转换为 OpenAI tools schema
            oai_tools = await get_oai_tools_from_mcp(mcp_session)

            while True:
                user_input = input("用户：").strip()
                if user_input.lower() in {"exit", "quit", "q", "退出"}:
                    print("再见 👋")
                    break

                # 每轮前做一下历史截断
                history = truncate_history(history)

                try:
                    await run_agent_once(
                        user_input,
                        history,
                        mcp_session=mcp_session,
                        oai_tools=oai_tools,
                    )
                except Exception as e:
                    print(f"\n[调用出错]: {e!r}\n")


def main():
    asyncio.run(chat_loop())


if __name__ == "__main__":
    main()
