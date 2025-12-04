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
现在假设你是一名高级数据增强工程师，需要根据以下“意图列表”生成用户可能提出的自然语言 Query。

【意图列表】
{INTENT_JSON}

你的任务是构建一个总量为 {TOTAL_NUM} 条的高质量、多样化用户 Query 数据集。每条数据需包含：
- "query": 自然语言文本
- "intent": 意图名称数组，内容来自 INTENT_JSON 的名称
- "label": 数组形式的意图编号，对应 INTENT_JSON 中的索引，可为单意图或多意图组合

### 生成要求：
1. 覆盖所有单一意图  
2. 覆盖所有意图组合（2/3意图组合；偶尔包含更多多意图）  
3. 表达方式高度多样化：口语、专业、非专业、模糊、长句短句混合、中英混杂等  
4. 真实用户风格：轻微错别字、语气词、口语表达、真实生活场景化  
5. 不同明确性等级：明确表达、间接表达、模糊表述  
6. 随机性：词序/句型/场景/风格随机，避免模板化  
7. 分布控制：每个意图40–80条、组合全覆盖、三意图组合≥20条、多意图组合≤15%  
8. 所有 Query 必须自然真实、符合真实用户场景  

---

### 输出格式（必须严格遵守）：

请将最终结果严格输出为 **JSON 数组（list）**，数组中的每个元素是一个对象，格式如下：

[
    {
        "query": "…", 
        "intent": ["意图名1", "意图名2"], 
        "label": [0, 3]
    },
    ...
]

严格要求：
- 只能输出 JSON 数组本身，不得添加任何注释、解释、额外文本  
- 不得使用 Markdown 代码块（如 ```）  
- JSON 必须合法  
- 所有 key 必须使用双引号  
- label 必须是数组，即使只有一个意图  
- 数组最后一项后不得有逗号  

---

### 注意：
你一次只输出用户要求的区间（start–end 对应条目），直到用户让你继续。
'''
).strip()

USER_PROMPT = dedent(
'''
现在请生成第 {{start}} 到第 {{end}} 条数据。
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

    
    pass