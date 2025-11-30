import os
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
functions = [
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


def chose_function_llm(prompt):
    response = llm_client.chat.completions.create(
        model="qwen3-max",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        stream=False,
        functions=functions
    )
    return response


if __name__ == "__main__":
    # prompt = "今天深圳天气怎么样？"
    while True:

        prompt = input("请输入: ")
        response = chose_function_llm(prompt)

        msg = response.choices[0].message

        if msg.function_call:
            func_name = msg.function_call.name
            args = msg.function_call.arguments  # 是 JSON 字符串
            import json
            args = json.loads(args)

            print("模型要求调用函数：", func_name, "参数：", args)

            # 调用真实函数
            result = get_weather(**args)

            print(result)
