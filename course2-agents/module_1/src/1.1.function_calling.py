
from typing import  Annotated
from openai import OpenAI

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key="sk-9f53ec0ec3234971af8af2c605c83c09",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# -----------------------------
# 定义：可供模型调用的函数
# -----------------------------

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



tools = [
    {
        "name": "get_weather",
        "description": "根据提供的城市，获取对应的天气",
        "parameters":
            {
                "type": "object",
                "properties": {

                    "city": {
                        "description": "城市名称",
                    }
                },
                "required": ["city"]
            }

    }
]


# -----------------------------
# 第 1 步：向模型发送带函数定义的请求
# -----------------------------

prompt = "今天深圳天气怎么样？"

response = client.chat.completions.create(
    model="qwen3-max",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ],
    stream=False,
    # tools=tools,
    functions=[
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
)

# -----------------------------
# 第 2 步：解析模型返回的 function_call
# -----------------------------
msg = response.choices[0].message

if msg.function_call:
    func_name = msg.function_call.name
    args = msg.function_call.arguments  # 是 JSON 字符串
    import json
    args = json.loads(args)

    print("模型要求调用函数：", func_name, "参数：", args)

    # 调用真实函数
    result = get_weather(**args)

    # -----------------------------
    # 第 3 步：把函数结果再发回模型
    # -----------------------------
    print("最终回复：", end="")
    
    final = client.chat.completions.create(
        model="qwen3-max",
        messages=[
            {"role": "user", "content": "今天深圳天气怎么样？"},
            msg,  # 模型的 function_call 消息
            {
                "role": "function",
                "name": func_name,
                "content": result,
            }
        ]
    )
    print(final.choices[0].message.content)
