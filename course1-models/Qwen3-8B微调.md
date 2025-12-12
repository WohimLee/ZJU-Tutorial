## Qwen3-8B
### 目标与原则
>目标

- 一套底座覆盖所有功能（可用、稳定、不掉通用）
- 关键强约束任务用 GRPO 拉满正确率（SQL/Cypher/FunctionCall/Slot）
- 自我认知不污染其他功能

>核心原则

- SFT 可以多任务混训（靠 task tag 区分）
- GRPO 必须按 reward 逻辑分阶段（别混）
- 通用能力靠三件事保住：
    - 通用数据注入（1%~5%）
    - reference+KL（必开）
    - 回归集红线（掉了就刹车）

### 方案总览（你最终会得到什么）

你最终产物建议是这些 Adapter（都是 LoRA/QLoRA）：

- Adapter-Base-SFT：多任务基础能力（覆盖面 + 稳定）
- Adapter-FC-GRPO：function call 强化
- Adapter-SLOT-GRPO：槽位抽取强化（如果你线上很依赖抽取准确率）
- Adapter-SQL-GRPO：text2sql 强化（执行正确率/结果正确率）
- Adapter-CYPHER-GRPO：text2cypher 强化
- Adapter-PERSONA-SFT（可选）：自我认知/风格，仅 SFT

部署时做任务路由加载：

- chat：Base + Persona
- function call：Base + FC
- slot：Base + SLOT
- text2sql：Base + SQL
- text2cypher：Base + CYPHER

### 阶段 0｜数据与评测体系（先建“刹车系统”）
#### 0.1 数据分桶（必须）

A. 多任务 SFT 训练集
B. 通用保形 SFT 集（小比例）
C. 各任务 GRPO prompts（可验证）
D. 通用回归集（只评估）
E. 各任务专项回归集（只评估）

#### 0.2 回归集红线（建议明确指标）

通用：指令遵循、多语、长文本理解、写作、知识问答、格式稳定性

专项：
- FC：schema 合法率、必填字段率、参数类型正确率
- SLOT：字段 F1 / schema 合法率
- SQL/Cypher：可执行率、结果匹配率、引用不存在表列率（越低越好）

规则：只要通用回归显著下降，就停止当前 GRPO 或加大 KL / 降 LR。

### 阶段 1｜模型与 LoRA 策略（保通用取向）

基座：qwen3-8B

训练形态：QLoRA（4bit 加载 + LoRA 训练）

LoRA 初始选择（保守稳）：
- target modules：q_proj, v_proj, o_proj（先不动 MLP）
- r=8~16，alpha=2r，dropout=0.05
- max_seq_len：按任务 2k/4k 起步（先别追超长）

### 阶段 2｜多任务 SFT（一次把“会做”铺开）
#### 2.1 统一输入输出协议（强烈建议）

每条样本都有 task tag（system 或 user 第一行）：

- [TASK=INTENT_REWRITE]
- [TASK=SLOT_JSON]
- [TASK=FUNCTION_CALL]
- [TASK=TEXT2SQL|DIALECT=POSTGRES]
- [TASK=TEXT2CYPHER|NEO4J=v5]

并把各任务输出格式写死（JSON schema / tool schema / SQL 方言约束）。

#### 2.2 SFT 数据混合比例（起点）

- intent rewrite：25%~40%
- slot：20%~30%
- function call：15%~25%
- text2sql：10%~20%
- text2cypher：5%~15%
- 通用保形 B：1%~5%（强烈建议）

注意：SQL/Cypher 样本里必须带 schema，否则幻觉会非常顽固。

#### 2.3 SFT 训练目标

- 格式基本稳定
- 各任务能跑通（不追峰值）
- 通用回归集不下降或微降可接受

产物：Adapter-Base-SFT

### 阶段 3｜Persona（自我认知）单独做（可选但推荐拆）

做法二选一：
- 优先方案：system prompt + 少量 SFT（最不污染）
- 或：训练一个 Adapter-PERSONA-SFT（只 SFT，不 RL）

原则：

- 不和 SQL/FC/Slot 混 GRPO
- 不把 persona 写成强规则覆盖所有任务（否则 function call 会变啰嗦）

### 阶段 4｜GRPO 分阶段强化（按 reward 分开训）

>所有 GRPO 共通配置：

- reference：冻结 Adapter-Base-SFT 作为 reference policy
- policy：从 Base-SFT 拷贝出来继续训
- KL 必开
- 每 N step 跑通用回归集（红线刹车）

#### 4.1 GRPO-1：Function Call 强化（Adapter-FC-GRPO）
##### reward（可全自动）

- JSON 可解析（0/1）
- 满足 tool schema（0/1）
- 必填字段齐全（0/1）
- 参数类型正确（0/1）
- 额外：不允许输出多余自然语言（违反扣分）

产物：Adapter-FC-GRPO

#### 4.2 GRPO-2：Slot 抽取强化（Adapter-SLOT-GRPO）（如果你需要）
##### reward

- JSON/schema 合法（0/1）
- 字段匹配（F1 或分段得分）
- 不得编造槽位值（引用不到就留空/unknown）

产物：Adapter-SLOT-GRPO

#### 4.3 GRPO-3：Text2SQL 强化（Adapter-SQL-GRPO）
##### reward（按你资源分两档）

##### 强验证（推荐）：执行 + 结果比对

- 能解析/能执行：+1
- 结果与 gold 一致：+2（或 +3）
- 引用不存在表列：-2（直接打 0 也行）

##### 弱验证（无 gold）：只做可执行 + 约束检查

- 能执行：+1
- 无不存在表列：+1
- 满足方言约束：+1

关键：prompt 必须带 schema；并且固定方言（先单方言，后扩展）。

产物：Adapter-SQL-GRPO

#### 4.4 GRPO-4：Text2Cypher 强化（Adapter-CYPHER-GRPO）

与 SQL 同理，只是执行环境换 Neo4j：

- 语法/编译通过
- 执行通过
- 结果一致（有 gold 最好）
- 不存在 label/relationship/property 惩罚

产物：Adapter-CYPHER-GRPO

### 阶段 5｜防通用能力回退（训练过程的“硬机制”）

你要把下面三件事写进训练 pipeline 里，不是口头说：

##### 1 通用保形注入

- SFT：1%~5% 通用指令/对话
- GRPO：也混入 1%~5% “通用 prompts”，但只用 KL（不给正向奖励）

##### 2 动态 KL / Early stop

- 通用回归下降 → 提高 KL / 降 LR / 停训
- 专项上升但通用掉得快 → 当前 GRPO 过猛

##### 3 PEFT 保守化

- 先不训 MLP
- r 不要一上来 64
- 学习率从小开始（GRPO 尤其要小）

### 阶段 6｜部署与路由（最终工程形态）
#### 路由策略（建议）

由上游分类器/规则判断任务类型：

- 有工具列表 → function call
- 有 schema + 要查询 → text2sql/cypher
- 要抽结构化字段 → slot
- 其他 → chat

#### 推理加载
- chat：Base + Persona（可选）
- fc：Base + FC
- slot：Base + SLOT
- sql：Base + SQL
- cypher：Base + CYPHER

如果你不想多 adapter 切换：至少保证 SQL/FC 这类“高强约束”有专用 adapter。