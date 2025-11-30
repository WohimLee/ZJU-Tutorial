#!/usr/bin/env python3
import asyncio
import json
from typing import Any, Dict, List, Optional

from openai import OpenAI

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPFunctionCallingAgent:
    """
    一个简单的 Agent：
    - 连接本地 MCP server（通过 stdio）
    - 使用 OpenAI Chat Completions
    - 让模型自动决定是否调用 MCP 工具（add / sub）
    """

    def __init__(
        self,
        model: str = "gpt-4.1-mini",
        server_command: str = "python",
        server_args: Optional[List[str]] = None,
    ) -> None:
        self.model = model
        self.client = OpenAI()  # OPENAI_API_KEY 从环境变量里读

        if server_args is None:
            server_args = ["mcp_calc_server.py"]

        # MCP stdio 服务参数
        self.server_params = StdioServerParameters(
            command=server_command,
            args=server_args,
        )

        # Agent 级别的对话记忆
        self.messages: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "你是一个会调用 MCP 工具的智能助手。"
                    "对于需要精确算术的任务，请优先调用 add / sub 工具，"
                    "然后用自然语言解释计算过程。"
                ),
            }
        ]

        # 提前定义好要暴露给模型的 tools schema
        self.tools: List[Dict[str, Any]] = [
            {
                "type": "function",
                "function": {
                    "name": "add",
                    "description": "对两个数字求和，返回 a + b（底层通过 MCP 服务器计算）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "第一个加数"},
                            "b": {"type": "number", "description": "第二个加数"},
                        },
                        "required": ["a", "b"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "sub",
                    "description": "对两个数字求差，返回 a - b（底层通过 MCP 服务器计算）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "被减数"},
                            "b": {"type": "number", "description": "减数"},
                        },
                        "required": ["a", "b"],
                    },
                },
            },
        ]

    # ---------------------- 对外暴露的主方法 ---------------------- #

    async def achat_once(self, user_message: str) -> str:
        """
        单轮对话：
        - 把用户消息加入 memory
        - 让模型自动决定要不要 function_call
        - 如果有 tool_call，就自动走 MCP server
        - 最后返回自然语言答案（并更新 memory）
        """
        self.messages.append({"role": "user", "content": user_message})

        # 每次调用时建立一个 MCP 会话（简单粗暴，但更好理解）
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as mcp_session:
                await mcp_session.initialize()

                # 1. 先问一次模型，看要不要调用工具
                assistant_msg = await self._call_llm_for_tools()

                # 把模型第一次回复加入对话（无论有没有 tool_calls）
                self.messages.append(self._msg_to_dict(assistant_msg))

                # 2. 如果没有工具调用，就直接返回
                if not assistant_msg.tool_calls:
                    return assistant_msg.content or ""

                # 3. 否则，用 MCP 真正执行这些工具
                tool_messages = await self._run_tool_calls(
                    mcp_session, assistant_msg.tool_calls
                )

                # 4. 再次调用模型，让它基于工具结果给出最终回答
                final_msg = self._call_llm_with_tools_result(tool_messages)

                # 更新 memory
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": final_msg.content,
                    }
                )

                return final_msg.content or ""

    def reset(self) -> None:
        """清空对话记忆（除了 system 提示）"""
        self.messages = [self.messages[0]]

    # ---------------------- 内部工具方法 ---------------------- #

    async def _call_llm_for_tools(self):
        """第一次调用 LLM，让它决定要不要用 tool"""
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=self.tools,
        )
        return resp.choices[0].message

    async def _run_tool_calls(self, mcp_session: ClientSession, tool_calls):
        """
        遍历所有 tool_calls，通过 MCP 服务器执行，
        然后构造 'tool' role 的消息列表返回。
        """
        tool_messages: List[Dict[str, Any]] = []

        for call in tool_calls:
            tool_name = call.function.name
            raw_args = call.function.arguments or "{}"
            args = json.loads(raw_args)

            # 调 MCP 工具
            result = await mcp_session.call_tool(
                tool_name,
                arguments=args,
            )

            # CallToolResult -> dict -> str（直接塞给 LLM）
            result_dict = result.model_dump()
            result_text = json.dumps(result_dict, ensure_ascii=False)

            tool_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": tool_name,
                    "content": result_text,
                }
            )

        # 把 tool 消息也并入内存
        self.messages.extend(tool_messages)
        return tool_messages

    def _call_llm_with_tools_result(self, tool_messages: List[Dict[str, Any]]):
        """工具执行完之后，再调用一次 LLM，让它生成最终回答"""
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
        )
        return resp.choices[0].message

    @staticmethod
    def _msg_to_dict(msg) -> Dict[str, Any]:
        """把 OpenAI 的 message 对象转成 messages 里用的 dict"""
        # 利用 SDK 自带的 to_dict()
        return msg.to_dict()


# ---------------------- 简单测试入口 ---------------------- #

async def _demo():
    agent = MCPFunctionCallingAgent(
        model="gpt-4.1-mini",
        server_command="python",
        server_args=["mcp_calc_server.py"],
    )

    ans = await agent.achat_once("请帮我算一下 123 和 456 的和，再解释一下怎么算出来的。")
    print("Agent:", ans)


if __name__ == "__main__":
    asyncio.run(_demo())
