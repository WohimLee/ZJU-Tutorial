
import asyncio
import json

from openai import OpenAI

from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.stdio import StdioServerParameters


# 你的 OpenAI 客户端
openai_client = OpenAI()


async def chat_with_tools(prompt: str):
    """
    让模型自动选择是否调用 add/sub 这两个 MCP 工具，
    然后拿到工具结果，再让模型生成最终回答。
    """
    # 1. 描述如何启动 MCP 服务器（刚才写的 mcp_calc_server.py）
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_calc_server.py"],  # 如果不在同一目录，要改成绝对路径
    )

    # 2. 建立到 MCP server 的 stdio 连接
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            # 初始化 MCP 协议（握手等）
            await mcp_session.initialize()

            # 3. 在 LLM 这边声明“工具 schema”（函数签名）
            #    注意：这里的 tools schema 是给 OpenAI 的，
            #    具体执行则由 mcp_session.call_tool 去调 MCP server
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "add",
                        "description": "对两个数字求和，返回 a + b（调用的是 MCP 服务器里的 add 工具）",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "a": {
                                    "type": "number",
                                    "description": "第一个加数",
                                },
                                "b": {
                                    "type": "number",
                                    "description": "第二个加数",
                                },
                            },
                            "required": ["a", "b"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "sub",
                        "description": "对两个数字求差，返回 a - b（调用的是 MCP 服务器里的 sub 工具）",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "a": {
                                    "type": "number",
                                    "description": "被减数",
                                },
                                "b": {
                                    "type": "number",
                                    "description": "减数",
                                },
                            },
                            "required": ["a", "b"],
                        },
                    },
                },
            ]

            # 会话消息列表
            messages = [
                {
                    "role": "system",
                    "content": "你可以调用工具 add 和 sub 来进行精确的数学计算，"
                               "工具负责算数，你负责解释计算过程。",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]

            # 4. 第一次调用模型：让模型决定要不要调用工具（tool_choice 默认 auto）
            first = openai_client.chat.completions.create(
                model="gpt-4.1-mini",  # 或 gpt-4.1 / gpt-4o 等
                messages=messages,
                tools=tools,
            )

            assistant_msg = first.choices[0].message
            messages.append(assistant_msg.to_dict())  # 把助手消息也放回 messages

            # 如果模型没有发起 tool_calls，就直接返回它的自然语言回答
            if not assistant_msg.tool_calls:
                print("模型没有调用任何工具：\n")
                print(assistant_msg.content)
                return

            print(f"模型发起了 {len(assistant_msg.tool_calls)} 个工具调用。")

            # 5. 逐个执行工具调用（通过 MCP server）
            for tool_call in assistant_msg.tool_calls:
                tool_name = tool_call.function.name
                raw_args = tool_call.function.arguments or "{}"
                args = json.loads(raw_args)

                print(f"\n[LLM 请求调用工具] {tool_name}({args})")

                # 调用 MCP 服务器里的工具
                result = await mcp_session.call_tool(tool_name, arguments=args)

                # CallToolResult 是一个 Pydantic 模型，我们简单转成 dict / str 给 LLM
                result_dict = result.model_dump()
                result_text = json.dumps(result_dict, ensure_ascii=False)

                print(f"[MCP 工具返回结果] {result_text}")

                # 构造 tool 消息，回填给 OpenAI，让模型基于工具结果继续思考
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": result_text,
                }
                messages.append(tool_message)

            # 6. 再次调用模型：这一次不再需要 tools，让它基于工具结果给出最终自然语言回答
            final_resp = openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
            )

            final_msg = final_resp.choices[0].message
            print("\n===== 模型最终回答 =====\n")
            print(final_msg.content)


async def main():
    # 你可以在这里改成任意中文问法试试，比如减法、组合运算等
    prompt = "请帮我计算 10 和 25 的和，并解释一下你是怎么算的。"
    await chat_with_tools(prompt)


if __name__ == "__main__":
    asyncio.run(main())
