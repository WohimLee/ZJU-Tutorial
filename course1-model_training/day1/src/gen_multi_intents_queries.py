import os
import json

from tqdm import tqdm
from openai import OpenAI
from textwrap import dedent
from dotenv import load_dotenv


from htsc.common.my_logger import logger


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
load_dotenv(os.path.join(f"{PROJECT_ROOT}", ".env"))


SYSTEM_PROMPT = dedent(
'''
现在假设你是一名高级数据增强工程师，需要根据以下“意图列表（Intents Map）”生成用户可能提出的自然语言 Query。

【意图列表】
{INTENT_JSON}

你的任务是构建一个总量为 {TOTAL_NUM} 条的高质量、多样化用户 Query 数据集。  
每条数据需包含以下字段：

{{
    "query": "用户真实自然语言文本",
    "sub_intent_id": ["子意图ID1", "子意图ID2", ...],
    "sub_intent_name": ["子意图名称1", "子意图名称2", ...]
}}

说明：  
- **所有意图均基于 INTENT_JSON 中的子意图列表**
- 不再需要一级意图字段  
- 多意图使用 **字符串列表（JSON 数组）**，例如：  
  "sub_intent_id": ["id1", "id2", "id3"]

------------------------------------------------------------

### ★ 生成要求（必须严格遵守）

#### 1. 意图覆盖
- 覆盖所有子意图（每个子意图至少 40–80 条）
- 覆盖所有两子意图组合
- 至少 20% 样本包含三子意图组合
- 多意图样本（≥4 个子意图）占比 ≤10%

> 意图组合必须语义合理：  
> ✔ 合理示例：行情查询 + 下单  
> ✘ 不合理示例：登录问题 + 财务分析  

#### 2. 表达方式多样
需模拟真实证券类用户表达，包括：

- 口语化表达、语气词（“啊”“呗”“咋办”“诶”等）
- 中英混杂（但中文为主）
- 新手与老手混合：专业术语 + 非专业模糊表达
- 情绪表达（担心、吐槽、兴奋等）
- 轻微错别字、可理解的语序错误
- 不同生活场景（通勤、复盘、交易中、朋友聊天等）
- 多种句式（短句、中句、长句）

#### 3. 自然性与随机性
- 避免模板化
- 股票名、指数名、行业名必须丰富，不得重复单一标的
- Query 不得出现 “意图、标签、模型、训练”等词
- 所有 Query 必须语义真实且不重复

#### 4. 字段规则（必须严格遵守）
- sub_intent_id 必须来自 INTENT_JSON 的子意图 id
- sub_intent_name 必须与子意图 name 完全一致
- 两者数量与顺序必须一一对应
- 多个标签必须为 JSON 字符串列表，例如：["A", "B", "C"]

------------------------------------------------------------

### ★ 输出格式（必须严格遵守）

最终输出必须是 **JSON 数组（list）**，结构如下：

[
  {{
    "query": "帮我看看今天大盘走势，顺便按昨晚收盘价买一点贵州茅台",
    "sub_intent_id": ["MARKET_INDEX_QUERY", "TRADE_CREATE_ORDER"],
    "sub_intent_name": ["指数行情查询", "发起下单请求"]
  }},
  ...
]

严格要求：
- **只能输出 JSON 数组，不得添加任何描述、注释或解释**
- **不能使用 Markdown 代码块（不能出现 ```）**
- 所有 key 必须使用双引号
- JSON 必须合法可解析
- 字符串列表必须使用 ["a", "b", "c"] 的格式
- 数组最后一项不能有逗号

------------------------------------------------------------

### ★ 增量生成机制
你一次只输出用户要求的区间（start–end 对应条目），直到我让你继续。
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


def gen_data(intent_map, start, end, N):

    system_prompt = SYSTEM_PROMPT.format(INTENT_JSON=intent_map, TOTAL_NUM=N)
    user_prompt = USER_PROMPT.format(start=start, end=end)
    logger.info(f"正在生成第 {start} 到第 {end} 条数据")
    completion = client.chat.completions.create(
        model="qwen3-max",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        stream=False
    )
    return completion.choices[0].message.content

with open(os.path.join(PROJECT_ROOT, "data/intent.json")) as f:
    intent_map = json.load(f)

step = 5
N = 10
for start in range(0, N, step):

    samples = gen_data(intent_map, start=start, end=start+step, N=N)
    try:
        samples = json.loads(samples)

        with open(os.path.join(PROJECT_ROOT, f"output/{start}_{start+step}.json"), "w") as f:
            json.dump(samples, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"😈生成错误: start={start}, end={start+step}")
        logger.exception(e)   # 自动带 traceback
        continue
pass

