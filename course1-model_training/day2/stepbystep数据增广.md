## stepbystep 数据增广

### 1 注册 LLM API

- [阿里云百炼](https://bailian.console.aliyun.com/&tab=doc?spm=5176.29597918.J_SEsSjsNv72yRuRFS2VknO.4.24757b08bTLwmd&tab=model#/model-market)

### 2 调试测试代码
>流式输出版本
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

>一次性输出
```py

```
### 3 利用大模型生成 Prompt

```
任务描述
部分要求
输出控制

帮我生成一个 system_prompt 和 user_prompt
```

### 4 结合 Prompt 生成代码

```
这是我的 Prompt:
这是我的 LLM API 调用代码示例: 
我的数据集在: 
帮我完善这个程序
```