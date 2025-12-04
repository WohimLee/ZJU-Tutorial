import os
import json

from tqdm import tqdm
from openai import OpenAI
from textwrap import dedent
from dotenv import load_dotenv


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
load_dotenv(os.path.join(f"{PROJECT_ROOT}", ".env"))



SYSTEM_PROMPT = dedent(
'''
你是一名高质量 NLU 数据生成器，任务是为意图识别模型创建训练数据。
以下为我们华泰证券 "AI涨乐APP" 业务部门定义的完整意图列表（系统记忆，不需在输出中重复）：
{INTENT_JSON}
请严格基于上述意图生成数据。
'''
).strip()

USER_PROMPT = dedent(
'''
你是一名高质量 NLU 数据生成器，任务是为意图识别模型创建训练数据。
请根据「意图：{INTENT_NAME}」生成 {N} 条用户可能说出的真实表达。

## 必须满足以下要求：
### (1) 多样化语言风格
- 每条表达需随机呈现不同语言风格，包括但不限于：
- 口语化
- 正式/书面
- 非专业表述
- 专业内的术语表达
- 省略句/不完整表达
- 有歧义但偏向该意图的表达
- 不同语气（请求、抱怨、疑惑、命令…）
- 不同措辞（换词、同义改写）

### (2) 表达内容约束
- 必须能真实地代表该意图
- 不得出现与其他意图混淆的语境
- 不加入模型提示痕迹（如“我是 AI...”）
- 不使用完全重复语义结构
- 像真人用户一样自然、多样、偶有口误

### (3) 输出格式
请将最终结果严格输出为 **JSON 数组（list）**，数组中的每个元素都是一个对象：
```
[
  {{
    "query": "用户表达1",
    "intent": "{INTENT_NAME}",
    "label": {INTENT_LABEL}
  }},
  {{
    "query": "用户表达2",
    "intent": "{INTENT_NAME}",
    "label": {INTENT_LABEL}
  }},
  ...
]
```
#### 注意：
- 只能输出一个 JSON 数组，不要输出其他任何解释文字
- 数组必须用中括号 [] 包裹
- 每个对象必须是合法 JSON
- 所有 key 必须用双引号 ""
- 最后一项后不能有逗号
'''
).strip()

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key=os.getenv("ALIBABA_API_KEY"),
    base_url=os.getenv("ALIBABA_API_URL"),
)


def gen_data(intent_map, intent, label, num=20):

    system_prompt = SYSTEM_PROMPT.format(INTENT_JSON=intent_map)
    user_prompt = USER_PROMPT.format(
                INTENT_NAME = intent,
                N = num,
                INTENT_LABEL = label
            )
    print(f"正在生成数据: intent: {intent}, label: {label}, num: {num}")
    completion = client.chat.completions.create(
        model="qwen3-max",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        stream=False
    )
    return completion.choices[0].message.content

with open(os.path.join(PROJECT_ROOT, "course1-models/data/intents_mapping.json")) as f:
    intent_map = json.load(f)

for key, value in intent_map.items():

    if int(key) >= 52:
        samples = gen_data(intent_map, intent=value, label=int(key))
        try:
            samples = json.loads(samples)

            with open(os.path.join(PROJECT_ROOT, f"course1-models/data/intents_data/intent_{int(key)}.json"), "w") as f:
                json.dump(samples, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"😈生成错误: intent: {value}, label: {key}")
            print(f"{e}")
            continue
    pass