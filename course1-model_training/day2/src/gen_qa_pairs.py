import os
import json
import time
from openai import OpenAI

# 初始化客户端（修复 base_url 末尾空格！）
client = OpenAI(
    api_key="sk-8cbfc6c6411a491d82c7151b14c313e9",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # ✅ 已移除末尾空格
)

# 原始文本（你提供的 Qwen3 技术文档）
text = """
## 大模型的诞生

### 🧭 一、大模型系列是怎么“诞生”的？

一个成熟的 LLM 系列从无到有大致会经历以下阶段：
<div align="center">
    <image src="imgs/llm_training_pipeline.png" width=>
</div>

#### 1. 确定目标与体系结构（Architecture Design）

团队首先决定：

- 模型类型：Decoder-only (LLM)、Encoder-only（Reranker）、Encoder-Decoder（某些任务）
- 模型大小：比如 1.8B、7B、32B、72B 等
- 模型功能：是否支持多语言、多模态、代码能力、长上下文等
- 训练方式：全量训练？增量？蒸馏？

Qwen 系列基于类似 GPT 的 Transformer Decoder-only 架构，并在 attention、position encoding 等方面进行了优化（比如 rope 多尺度化、缓存优化等）。

### 🧪 二、预训练 Base 模型：全系列的核心
#### Base 模型是什么？

Base（基础）模型是 未经指令微调的纯语言模型。
它的能力来源于大量无监督文本训练，如：网页、书籍、代码、论文、社区讨论、多语言数据

#### Base 的训练步骤
##### 1. 构建海量语料（Data Pipeline）

数据会经过：去重、质量评估、脏词过滤、格式规范化、语言检测、专业语料扩张（法律、医学、数学、代码）

Qwen3 的训练据公开信息使用了大量中文与英文数据，并通过 mixture-of-quality 技术控制不同数据对最终模型的影响。

##### 2. 自监督训练（Pretraining）

目标函数通常是：让模型预测下一个 token（Next-token Prediction）

Base 模型在这个阶段“习得”：语言理解、知识储备、推理能力、世界常识、代码结构感

这和 ChatGPT 的 GPT-3/3.5 Base 阶段类似。

结果就是产生了 Qwen3-0.6B、1.7B、8B、14B、32B 等 Base 模型。

### 🧩 三、指令微调（SFT）：让模型变“有用”

Base 模型只懂语言，不懂人类交互。于是要进行 Supervised Fine-Tuning (SFT)。

SFT 数据包括：问答数据（QA）、多轮对话、代码任务、数学推理、工程推理、角色扮演、应用场景指令

模型通过SFT学习“按照人类需求回答问题”的方式，从而诞生：Qwen3-Instruct 系列，例如：Qwen3-8B-Instruct、Qwen3-32B-Instruct。


### 🎚 四、偏好对齐（DPO / PPO / RLHF）

SFT 可以教模型“怎么回答”，但无法保证：安全性、礼貌度、合理性、稳定性、不胡说

因此加入对齐训练，例如：
- RLHF：强化学习（PPO）方式让模型根据人类偏好改变行为
- DPO：近年来更流行，直接用偏好数据优化模型

此阶段会产生 对齐后的 Chat 模型（例如 Qwen3-Chat）


#### 对齐三阶段（业界常用）
>① SFT（Supervised Fine-tuning）
- 监督微调：用高质量回答示范（Demonstration）

>② RLHF（Reinforcement Learning from Human Feedback）
- 用人为偏好训练 Reward Model，再做策略优化

>③ DPO、ORPO、PPO 等更高效的对齐技术
- 以更低成本实现“偏好对齐”

### 🔎 五、Embedding 模型从哪里来？
Embedding 模型不是 Base 的简单裁剪，而是 **重新训练** 或 **迁移训练的 Encoder 模型**

用途：向量检索（RAG）、文本相似度、语义分类、搜索排序

大多数 embedding 模型使用 双向 Transformer Encoder（类似 BERT），而不是 Decoder-only。

Embedding 的来源：
- 从头训练一个 Encoder 模型
- 从 Base 模型蒸馏得到 Encoder
- 用对比学习（contrastive learning）训练

Qwen3 的 embedding 多采用：
- 对比学习
- 大规模文本对齐数据
- 多语言表示优化

### ⚖️ 六、Reranker 是如何产生的？

Reranker 通常是 Cross-Encoder，输入为 `query + candidate`，输出一个相关性分数。

它的训练方式：
- 使用大量标注好的 `(query, passage, relevance)` 数据
- 采用 `pairwise / listwise` ranking loss
- 也可能蒸馏一个大模型（如 Qwen3-72B）

作用：
- 检索排序
- 问答系统的重新排序（RAG 中使用）
- 做推理判断（例如判断哪段理由最合理）

Reranker 通常比 embedding 更“重”，但更准确。

Qwen3-Reranker 也是这样产生的。

### 👁 七、Vision（多模态）模型又是怎么来的？

Vision LLM（如 Qwen-VL）通常来自：

#### 1. 训练一个视觉编码器（ViT、EfficientViT 等）

输入图片 → 输出向量。

#### 2. 做多模态对齐（Projection）

把视觉特征投影到语言空间。

#### 3. 用混合数据训练：
OCR 图片、图文配对、表格、UI截图、数学图形、文档图像

最终集成到大模型形成：Qwen3-VL（视觉语言模型）

### 🧱 八、一个 LLM 系列如何“扩展成全家桶”？

以 Qwen3 为例：

| 模型类型                | 用途    | 训练方式                |
| ------------------- | ----- | ------------------- |
| Base                | 纯语言理解 | 大规模无监督训练            |
| Chat                | 对话、应用 | Base + SFT + 对齐     |
| Math/Code/Reasoning | 专项强化  | 领域数据再训练             |
| Embedding           | 语义向量  | Encoder + 对比学习      |
| Reranker            | 排序判断  | Cross-Encoder 排序训练  |
| VL                  | 图像理解  | Vision 编码器 + LLM 对齐 |
| Audio/Speech        | 音频理解  | 声学模型 + LLM          |


一个大模型生态最终形成 多模型协同工作 的产品族。

### 📦 九、为什么要有多个参数规模？

不同参数规模对应不同应用场景：
- 小模型（1-4B） → 本地端侧部署
- 中模型（7-14B） → 中等推理能力、平衡成本
- 大模型（30-70B） → 强推理、长上下文、高质量生成
- 超大模型（100B+） → 专注极致性能（如 Qwen3-max 级别）

### 🧠 十、把整个流程串起来（总图）

→ 1. 收集和清洗海量数据
→ 2. 训练 Base 模型
→ 3. 做 SFT 得到 Chat 模型
→ 4. 做 RLHF/DPO 对齐优化
→ 5. 训练额外的 Embedding / Reranker / Vision 模型
→ 6. 蒸馏、量化、压缩，形成不同参数规模
→ 7. 发布完整的模型家族（如 Qwen3 系列）
"""

N = 20  # 总共生成 100 条 QA 对
BATCH_SIZE = 5

# System Prompt（全局设定，包含总条数）
system_prompt = f'''你是一位专业的 QA 对生成专家，正在协助完成一个总规模为 {N} 条的问答对挖掘任务。
所有问答对必须严格基于用户后续提供的原始文本生成，且满足以下要求：
1. **答案必须忠实于原文**：只能使用文本中明确出现的信息，或可直接、无歧义推断的内容；
2. **全程避免重复**：无论是问题措辞、语义角度还是信息点，都不能与已生成的任何 QA 对重复；
3. **最大化多样性**：针对同一信息点，应从不同提问角度（如“如何”“为何”“是否”“哪个”“怎么获取”“推荐什么”等）设计问题；
4. 问题需自然、口语化，符合真实用户提问习惯，避免机械模板；
5. 每条 QA 对必须独立、简洁、信息明确；
6. 输出格式：**仅允许 JSONL** —— 每行一个 JSON 对象，格式为 {{"question": "...", "answer": "..."}};
7. **禁止任何额外内容**：不输出说明、序号、空行、反引号、Markdown、列表符号等。

你将始终保持对“已生成内容”的警惕，主动创新问法，确保最终 {N} 条 QA 对高度多样且不重复。
'''

user_prompt_template = '''当前任务进度：正在生成第 {start}–{end} 条 QA 对（本批次共 {batch_size} 条）。

请基于以下原始文本，生成**全新且不重复**的问答对：
- 务必避免使用之前批次已出现的提问方式或语义角度；
- 即使信息点有限，也请通过变换句式、疑问词、语境（如操作指引、原因询问、确认类问题等）提升多样性；
- 所有答案必须可从以下文本中直接找到或明确推断。

原始文本：
{text}

【输出要求】
- 严格输出 {batch_size} 行；
- 每行格式：{{"question": "...", "answer": "..."}}
- 不含任何其他字符（包括空行、注释、序号等）。
'''

def parse_qa_lines(raw_output: str):
    lines = raw_output.strip().splitlines()
    qa_list = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            qa = json.loads(line)
            if "question" in qa and "answer" in qa:
                qa_list.append(qa)
            else:
                print(f"警告：第 {i+1} 行缺少字段: {line}")
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败（第 {i+1} 行）: {line} | 错误: {e}")
    return qa_list

def generate_qa_batch(start: int, end: int, batch_size: int, max_retries=3):
    user_prompt = user_prompt_template.format(
        start=start,
        end=end,
        batch_size=batch_size,
        text=text
    )
    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model="qwen3-max",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                stream=False,
                timeout=30
            )
            content = completion.choices[0].message.content
            qa_list = parse_qa_lines(content)
            if len(qa_list) == batch_size:
                return qa_list
            else:
                print(f"第 {start}-{end} 批：期望 {batch_size} 条，实际 {len(qa_list)} 条，重试...（第 {attempt+1} 次）")
        except Exception as e:
            print(f"第 {start}-{end} 批：API 调用失败，重试中... 错误: {e}")
        time.sleep(1)
    # 若失败，返回已解析的部分或空列表
    return qa_list[:batch_size]

# 主程序：按 0-5, 5-10, ..., 95-100 生成
all_qa = []

with open("qa_pairs.jsonl", "w", encoding="utf-8") as f:
    for i in range(0, N, BATCH_SIZE):
        start = i + 1
        end = min(i + BATCH_SIZE, N)
        current_batch_size = end - i

        print(f"正在生成第 {start}–{end} 条 QA 对...")
        qa_batch = generate_qa_batch(start, end, current_batch_size)

        for qa in qa_batch:
            if len(all_qa) < N:
                f.write(json.dumps(qa, ensure_ascii=False) + "\n")
                all_qa.append(qa)

        time.sleep(0.5)  # 防止 API 限流

print(f"✅ 成功生成并保存 {len(all_qa)} 条 QA 对到 qa_pairs.jsonl")