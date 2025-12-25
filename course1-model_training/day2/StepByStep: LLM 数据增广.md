## Step By Step

### 1 注册 LLM API
- [阿里云百炼](https://bailian.console.aliyun.com/&tab=doc?spm=5176.29597918.J_SEsSjsNv72yRuRFS2VknO.4.24757b08bTLwmd&tab=model#/model-market)
- [DeepSeek](https://platform.deepseek.com/usage)
- [Doubao](https://console.volcengine.com/ark/region:ark+cn-beijing/model/detail?Id=doubao-seed-1-6)

阿里云新用户免费

### 2 使用示例代码跑通大模型调用

>Qwen3
```py
import os
from openai import OpenAI

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
completion = client.chat.completions.create(
    model="qwen3-max",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "你是谁？"},
    ],
    stream=True
)
for chunk in completion:
    print(chunk.choices[0].delta.content, end="", flush=True)
```

### 3 生成 prompt

目的+示例代码

