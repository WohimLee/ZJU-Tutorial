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
tools = [
    {
        "name": "get_weather",
        "description": "查询某个城市的天气",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"}
            },
            "required": ["city"]
        },
    }
]


def chat_with_llm(prompt):
    response = llm_client.chat(
        model="qwen3-max",
        messages=[
            {"role": "system", "content": "请根据提供的工具，回复用户,工具如下：", "tools": tools},
            {"role": "user", "content": prompt},
        ],
        stream=False
    )
    return response


def final_summerize(prompt, fc_msg, weather_result):
    """
    使用流式输出的方式，在终端实时打印大模型最终回复。
    同时返回完整的回复字符串。
    """

    final_stream = llm_client.chat.completions.create(
        model="qwen3-max",
        messages=[
            {"role": "user", "content": prompt},
            fc_msg,  # 模型的 function_call 消息
            {
                "role": "function",
                "name": fc_msg.function_call.name,
                "content": weather_result,
            }
        ],
        stream=True
    )

    full_content = ""
    for chunk in final_stream:
        delta = chunk.choices[0].delta
        content = getattr(delta, "content", None) or ""
        if content:
            print(content, end="", flush=True)
            full_content += content

    return full_content


if __name__ == "__main__":
    # prompt = "今天深圳天气怎么样？"
    while True:

        prompt = input("请输入: ")
        fc_response = chose_function_llm(prompt)

        fc_msg = fc_response.choices[0].message
        func_name = fc_msg.function_call.name
        args = fc_msg.function_call.arguments  # 是 JSON 字符串
        args = json.loads(args)
        print("模型要求调用函数：", func_name, "参数：", args)

        weather_result = get_weather(**args)

        print("最终回复：", end="", flush=True)
        final_response = final_summerize(prompt, fc_msg, weather_result)
        print()
