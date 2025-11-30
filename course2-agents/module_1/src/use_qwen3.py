

import os
from openai import OpenAI

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key=os.getenv("ALIBABA_API_KEY"),
    base_url=os.getenv("ALIBABA_API_URL"),
)

tools = []
prompt = ""

completion = client.chat.completions.create(
    model="qwen3-max",
    messages=[
        {"role": "system", "content": "请根据提供的工具，回复用户,工具如下："},
        {"role": "user", "content": prompt},
    ],
    stream=True,
    tools=tools
)
for chunk in completion:
    print(chunk.choices[0].delta.content, end="", flush=True)