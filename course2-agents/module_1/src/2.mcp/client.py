import os
import json
import asyncio

from dotenv import load_dotenv
load_dotenv("/Users/azen/Desktop/llm/ZJU-Tutorial/.env")

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from openai import OpenAI



# 你的 OpenAI / 百炼客户端（和 5.function_calling_more_tools.py 中类似）
llm_client = OpenAI(
    api_key=os.getenv("ALIBABA_API_KEY"),
    base_url=os.getenv("ALIBABA_API_URL")
)

tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "查询某个城市的天气",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称",
                        }
                    },
                    "required": ["city"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_info_by_tavily",
                "description": "Tavily 搜索 API，搜索相关信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "用户想要搜索的内容",
                        }
                    },
                    "required": ["query"],
                },
            },
        },
    ]

async def chat_with_llm(prompt: str) -> None:
    """
    通过 MCP server 调用 get_weather / search_info_by_tavily 两个工具，
    整体流程与 5.function_calling_more_tools.py 类似，只是把工具放到了 MCP server 里。
    """

    server_params = StdioServerParameters(
        command="python",
        # 假设你在 src/2.mcp 目录下运行本文件，如：
        #   cd course2-agents/module_1/src/2.mcp && python client.py
        # 如果工作目录不同，这里的相对路径需要自己调整。
        args=["server.py"],
    )

    messages = [
        {
            "role": "system",
            "content": "请根据提供的工具，回复用户,工具如下：",
        },
        {"role": "user", "content": prompt},
    ]

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            await mcp_session.initialize()

            # 第一次调用模型，让它决定是否调用 MCP 工具
            first = llm_client.chat.completions.create(
                model="qwen3-max",
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            assistant_msg = first.choices[0].message
            messages.append(assistant_msg.to_dict())

            # 如果没有工具调用，直接打印模型回答
            if not assistant_msg.tool_calls:
                print(assistant_msg.content or "")
                return

            # 有工具调用时，通过 MCP server 真正执行
            for tool_call in assistant_msg.tool_calls:
                tool_name = tool_call.function.name
                raw_args = tool_call.function.arguments or "{}"
                args = json.loads(raw_args)

                print(f"[LLM 请求调用工具] {tool_name}({args})")

                result = await mcp_session.call_tool(tool_name, arguments=args)
                result_text = json.dumps(result.model_dump(), ensure_ascii=False)

                print(f"[MCP 工具返回结果] {result_text}")

                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": result_text,
                }
                messages.append(tool_message)

            # 第二次调用模型，让模型基于工具结果给出最终答案
            final = llm_client.chat.completions.create(
                model="qwen3-max",
                messages=messages,
                tool_choice="none",
            )
            final_msg = final.choices[0].message
            print(final_msg.content or "")


async def main() -> None:
    prompt = input("请输入: ")
    await chat_with_llm(prompt)


if __name__ == "__main__":
    asyncio.run(main())

