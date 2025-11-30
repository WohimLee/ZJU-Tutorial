import os
import json

from typing import  Annotated
from openai import OpenAI

llm_client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key=os.getenv("ALIBABA_API_KEY"),
    base_url=os.getenv("ALIBABA_API_URL"),
)


def get_weather(city: Annotated[str, 'The name of the city to be queried', True]):
    """
    Get the current weather for `city_name`
    """

    if not isinstance(city, str):
        raise TypeError("City name must be a string")

    key_selection = {
        "current_condition": ["temp_C", "FeelsLikeC", "humidity", "weatherDesc", "observation_time"],
    }
    import requests
    try:
        resp = requests.get(f"https://wttr.in/{city}?format=j1")
        resp.raise_for_status()
        resp = resp.json()
        ret = {k: {_v: resp[k][0][_v] for _v in v} for k, v in key_selection.items()}
    except:
        import traceback
        ret = "Error encountered while fetching weather data!\n" + traceback.format_exc()

    return str(ret)

# 注册登记函数
# functions = [
#     {
#         "name": "get_weather",
#         "description": "查询某个城市的天气",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "city": {"type": "string", "description": "城市名称"}
#             },
#             "required": ["city"]
#         },
#     }
# ]

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
    }
]


def chat_with_llm(prompt):
    history = [
        {
            "role": "system",
            "content": "请根据提供的工具，回复用户（可以自动选择和多次调用工具），工具如下："
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    # 假设要多次调用工具
    while True:
        
        response = llm_client.chat.completions.create(
            model="qwen3-max",
            messages=history,
            tools=tools,
            tool_choice="auto",
            # stream=True
        )
        msg = response.choices[0].message

        # 如果有工具调用
        if msg.tool_calls:
            # 先把 assistant 这条带 tool_calls 的消息加入 history
            history.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": msg.tool_calls,
            })

            # 逐个执行工具并把结果回填到 history
            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments or "{}")

                tool_result = eval(f"{tool_name}(**tool_args)")

                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": str(tool_result),
                })
            # 回填完工具结果后，继续 while True，进入下一轮模型调用
            continue

        # 没有 tool_calls 了，说明是最终回答
        else:
            history.append({
                "role": "assistant",
                "content": msg.content or "",
            })
            break

    full_content = ""
    for chunk in response:
        delta = chunk.choices[0].delta
        content = getattr(delta, "content", None) or ""
        if content:
            print(content, end="", flush=True)
            full_content += content
    print()
    return full_content



if __name__ == "__main__":
    # prompt = "今天深圳天气怎么样？"
    while True:

        prompt = input("请输入: ")
        print("LLM：", end="", flush=True)
        chat_with_llm(prompt)
