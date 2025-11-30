import os
import json

from typing import  Annotated
from openai import OpenAI

'''
一轮工具调用 + 一次总结
'''

llm_client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key=os.getenv("ALIBABA_API_KEY"),
    base_url=os.getenv("ALIBABA_API_URL"),
)

HISTORY = [
    {
        "role": "system", 
        "content":  "请根据提供的工具，回复用户（可以自动选择和多次调用工具），工具如下："
    }
]


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


def chose_tool_llm(prompt):

    HISTORY.append(
        {"role": "user", "content": prompt}
    )
    response = llm_client.chat.completions.create(
        model="qwen3-max",
        messages=HISTORY,
        tools=tools,
        tool_choice="auto",
        stream=False
    )
    return response



def final_summerize(history):
    """
    使用流式输出的方式，在终端实时打印大模型最终回复。
    同时返回完整的回复字符串。
    """

    final_stream = llm_client.chat.completions.create(
        model="qwen3-max",
        messages=history,
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



if __name__ == "__main__":
    # prompt = "今天深圳天气怎么样？"
    while True:

        prompt = "今天深圳天气怎么样？" # input("请输入: ")
        tool_response = chose_tool_llm(prompt)

        tool_msgs = tool_response.choices[0].message
        HISTORY.append({
                "role": "assistant",
                "content": tool_msgs.content or "",
                "tool_calls": tool_msgs.tool_calls or "",
            })

        if tool_msgs.tool_calls:
            
            for tool_call in tool_msgs.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # 在本地执行函数
                print("模型要求调用函数：", tool_name, "参数：", tool_args)
                tool_res = eval(f"{tool_name}(**tool_args)")

                HISTORY.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_res,
                    }
                )


        print("LLM：", flush=True)
        final_response = final_summerize(history=HISTORY)

        break