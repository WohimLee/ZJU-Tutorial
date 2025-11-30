import os
import json
import asyncio

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from openai import OpenAI


# 加载环境变量（根据你的项目路径调整）
load_dotenv("/Users/azen/Desktop/llm/ZJU-Tutorial/.env")

llm_client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key=os.getenv("ALIBABA_API_KEY"),
    base_url=os.getenv("ALIBABA_API_URL"),
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
                    "city": {"type": "string", "description": "城市名称"}
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
                    "query": {"type": "string", "description": "用户想要搜索的内容"}
                },
                "required": ["query"],
            },
        },
    },
]


async def chat_with_llm(prompt: str) -> str:
    """
    基于 MCP server 调用 get_weather / search_info_by_tavily，
    流程与原来的本地函数工具调用一致，只是工具实现搬到了 MCP。
    """

    history = [
        {
            "role": "system",
            "content": "请根据提供的工具，回复用户,工具如下：",
        }
    ]

    messages = history + [{"role": "user", "content": prompt}]

    # 第一步：让大模型决定是否调用工具（非流式）
    fc_response = llm_client.chat.completions.create(
        model="qwen3-max",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        stream=False,
    )

    fc_msg = fc_response.choices[0].message

    # 未触发工具调用，直接用流式输出生成回复
    if not fc_msg.tool_calls:
        final_stream = llm_client.chat.completions.create(
            model="qwen3-max",
            messages=messages,
            stream=True,
        )

        full_content = ""
        for chunk in final_stream:
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None) or ""
            if content:
                print(content, end="", flush=True)
                full_content += content
        print()
        return full_content

    # 有工具调用：通过 MCP server 调用工具
    server_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "2.mcp",
        "server.py",
    )

    server_params = StdioServerParameters(
        command="python",
        args=[server_path],
    )

    messages.append(
        {
            "role": "assistant",
            "tool_calls": fc_msg.tool_calls,
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            await mcp_session.initialize()

            for tool_call in fc_msg.tool_calls:
                tool_name = tool_call.function.name
                raw_args = tool_call.function.arguments or "{}"
                func_args = json.loads(raw_args)

                print(f"\n模型要求调用 MCP 工具：{tool_name} 参数：{func_args}")

                result = await mcp_session.call_tool(
                    tool_name,
                    arguments=func_args,
                )
                result_text = json.dumps(result.model_dump(), ensure_ascii=False)

                # print(f"MCP 工具返回结果：{result_text}\n")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": result_text,
                    }
                )

    # 第二步：使用流式输出的方式获取大模型最终回复
    final_stream = llm_client.chat.completions.create(
        model="qwen3-max",
        messages=messages,
        stream=True,
        tool_choice="none",  # 最终回复阶段不再调用工具
    )

    full_content = ""
    for chunk in final_stream:
        delta = chunk.choices[0].delta
        content = getattr(delta, "content", None) or ""
        if content:
            print(content, end="", flush=True)
            full_content += content
    print()
    return full_content


async def main() -> None:
    while True:
        prompt = input("请输入: ")
        if not prompt:
            continue
        print("LLM：", end="", flush=True)
        await chat_with_llm(prompt)


if __name__ == "__main__":
    asyncio.run(main())
