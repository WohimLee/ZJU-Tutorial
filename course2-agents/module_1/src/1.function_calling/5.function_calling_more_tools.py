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

def search_info_by_tavily(query):
    from tavily import TavilyClient
    client = TavilyClient(os.getenv("TAVILY_API_KEY"))
    response = client.search(
        query=query
    )
    return json.dumps(response, ensure_ascii=False)


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
    }
]



def chat_with_llm(prompt):

    history = [
        {
            "role": "system",
            "content": "请根据提供的工具，回复用户,工具如下："
        }
    ]

    # 第一步：让大模型决定是否调用工具（非流式）
    fc_response = llm_client.chat.completions.create(
        model="qwen3-max",
        messages=history + [{"role": "user", "content": prompt}],
        tools=tools,
        tool_choice="auto",
        stream=False,
    )

    fc_msg = fc_response.choices[0].message

    # 如果触发了工具调用
    if fc_msg.tool_calls:
        tool_call = fc_msg.tool_calls[0]
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)

        # 在本地执行函数
        print("模型要求调用函数：", func_name, "参数：", func_args)
        fun_res = eval(f"{func_name}(**func_args)")

        # 构造包含工具调用与工具结果的完整对话历史
        messages = history + [
            {"role": "user", "content": prompt},
            {
                "role": "assistant",
                "tool_calls": fc_msg.tool_calls,
            },
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": fun_res,
            },
        ]

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

    # 未触发工具调用，直接用流式输出生成回复
    final_stream = llm_client.chat.completions.create(
        model="qwen3-max",
        messages=history + [{"role": "user", "content": prompt}],
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



if __name__ == "__main__":
    # prompt = "今天深圳天气怎么样？"
    while True:

        prompt = input("请输入: ")
        print("LLM：", end="", flush=True)
        chat_with_llm(prompt)
