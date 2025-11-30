

import json

from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.stdio import StdioServerParameters
from openai import OpenAI

llm_client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key="sk-9f53ec0ec3234971af8af2c605c83c09",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 一直干活，卡住当前线程，直到 return
# async def 定义的是“协程函数”：不会立刻执行完，而是返回一个“任务对象”，需要在事件循环里跑
async def chat_with_tools(prompt: str):
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_calc_server.py"],
    )

    tools = [
        {
            "type": "function",
            "function": {
                "name": "add",
                "description": "对两个数字求和",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"},
                    },
                    "required": ["a", "b"],
                },
            },
        },
    ]

    messages = [
        {"role": "system", "content": "你可以用 add 做精确加法。"},
        {"role": "user", "content": prompt},
    ]

    # 相当于启动一个子进程：python mcp_calc_server.py
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            await mcp_session.initialize()

            first = llm_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
                tools=tools,
            )
            assistant_msg = first.choices[0].message
            messages.append(assistant_msg.to_dict())

            # 不调用工具，直接回答
            if not assistant_msg.tool_calls:
                print(assistant_msg.content)
                return

            # 只处理第一个工具调用
            tool_call = assistant_msg.tool_calls[0]
            args = json.loads(tool_call.function.arguments or "{}")

            result = await mcp_session.call_tool("add", arguments=args)
            result_text = json.dumps(result.model_dump(), ensure_ascii=False)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": "add",
                "content": result_text,
            })

            final_resp = llm_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
            )
            print(final_resp.choices[0].message.content)
