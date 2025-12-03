## 课程大纲：Day 1 —— 大模型训练、微调基础
>课程目标

- 理解大模型训练全流程、PEFT、LoRA/QLoRA
- 掌握对比学习的核心思想及其在语义向量学习中的价值
- 理解并使用 FlagEmbedding（如 BGE、Jina Embedding 等）
- 完成一次微调任务（分类/指令微调/向量模型微调）
- 掌握 GUI 或 Python 两种操作方式


### 1. 理论模块（Theory）
#### 1.1 大模型训练与微调流程
- 数据准备 → 训练 → 评估 → 部署的标准流程
- 预训练与微调的区别
- 模型对齐（Alignment）与指令微调（Instruction Tuning）简介

#### 1.2 迁移学习与 PEFT（参数高效微调）
- 为什么需要 PEFT：成本、显存、工程效率
- 常见 PEFT 方法：LoRA、QLoRA、Adapter、Prefix Tuning 等

#### 1.3 LoRA / QLoRA 原理与适用场景

- LoRA 的低秩分解思想
- QLoRA 的 4-bit 量化机制
- 两者的优缺点与典型使用场景

#### 1.4 对比学习基础（Contrastive Learning）

- 对比学习的核心思想：拉近正样本，推远负样本
- 在 NLP 中的作用：
    - 语义相似度学习
    - 向量检索（RAG）
    - 文本匹配（如 query ↔ document）
- 常见范式：
    - Siamese / 双塔结构
    - In-batch neg / hard negative
- 对比学习 vs 指令微调：适用场景差异、性能对比


### 2. 案例讲解（Case Study）
#### 2.1 LoRA 微调案例

基于 Qwen3-8B 做分类或指令微调。

#### 2.2 对比学习 + PEFT 实战案例

- 使用 BGE 进行语义检索向量训练
- 训练数据格式：`query, positive passage, negative passage`
- 对比学习损失查看与可视化（margin loss / cosine similarity）
- 效果评估方式：
    - 检索命中率（Recall@k）
    - 向量可视化（TSNE）

#### 2.3 全参数 vs LoRA vs 对比学习向量微调对比

- 全参数微调：适用于生成任务
- LoRA 微调：适合指令微调
- 对比学习微调：适合检索场景
- 三者的显存、数据量、效果各自优势

### 3 实操环节（Hands-on Lab）
#### 3.1 无 Python 基础学员路径
>工具：可视化/低代码平台
- LLaMA-Factory UI

>实操内容
- 上传训练数据
- 选择预训练模型与微调方法
- 设置 LoRA 配置（r、alpha、dropout 等）
- 配置训练参数（epochs、batch size、lr 等）
- 启动训练任务并查看日志/结果

#### 3.2 有 Python 基础学员
##### A. LoRA 微调
>工具
- LlamaFactory
>实操内容
- 数据集准备
    - 加载 JSON/CSV 数据
    - 文本清洗、格式转化、数据划分
- LoRA 配置
    - 选择目标层
    - 配置 LoRA 超参数
    - QLoRA 的量化参数（4bit quantization config）
- 训练脚本编写
    - 使用 LlamaFactory 的快速启动方式
- 训练与调试
    - 启动训练
    - 查看 loss、learning rate、eval metric 等日志
    - 保存与加载微调后模型



##### B.Embedding 的微调
>工具
- sentence-transformers（或 FlagEmbedding 等）
- transformers / peft（可选，用于更底层自定义）
- FAISS / Milvus / Chroma 等向量库（用于检索评估）

>实操内容

- 数据集准备
    - 构造「query-文档」正负样本
        - 从现有 QA / 搜索日志里抽取 (query, positive_doc)
        - 通过 BM25 / 现有向量检索挖 hard negative（负样本）
    - 转成训练所需格式
        - pair 格式：(query, positive)
        - triple 格式：(query, positive, negative)
- 模型与损失函数选择
    - 选择合适的预训练 Embedding 模型（如通用中文/多语言 Embedding 模型）
    - 依据任务选择损失
        - MultipleNegativesRankingLoss（对比学习InfoNCE Loss）
        - TripletLoss / ContrastiveLoss 等
- 训练脚本编写
    - 使用 sentence-transformers
        - 定义 Dataset / Dataloader
        - 选择 base model、max_seq_length、batch size
        - 配置 optimizer、learning rate、warmup、训练轮数
    - 编写训练主循环或使用 SentenceTransformer.fit()
- 训练与调试
    - 观察训练过程中 loss 曲线是否收敛
    - 监控 GPU 显存、训练速度，适当调整 batch size / seq_length
- 效果评估与验证
    - 使用小型测试集构建简单检索流程
        - 向量化 query 与文档，使用 FAISS / 相似度搜索
        - 计算 Recall@K / MRR / nDCG 等指标
    - 对比「微调前 vs 微调后」Embedding 效果
- 模型保存与部署
    - 导出 SentenceTransformer 模型（保存到本地 / 云端）
    - 编写推理脚本
        - 批量向量化接口
        - 与现有检索（向量库）服务对接示例

##### C.Reranker 的微调
>工具

- sentence-transformers 的 CrossEncoder
- transformers（需要更细粒度控制时使用）
- 简单检索评估工具（如 pytrec_eval 或自写指标计算脚本）

>实操内容

- 数据集准备
    - 构造排序训练数据
        - 格式：(query, doc, label)
            - label 可为 0/1（相关 / 不相关）或打分（0–3 等级）
    - 负样本构造
        - 随机负样本：从未标注相关的文档中随机采样
        - hard negative：使用 Embedding 检索得到的高分但实际不相关文档
- 模型选择与任务定义
    - 选择预训练 Reranker 模型（如通用中文 cross-encoder / reranker 模型）
    - 明确训练目标：
        - 二分类 (relevant / non-relevant)
        - 回归打分（学习相关性分数）
- 训练脚本编写
    - 使用 CrossEncoder 进行训练
        - 构造训练样本列表：(text_pair, label)
        - 选择损失函数：
            - BCEWithLogitsLoss（用于二分类）
            - MSELoss / MarginRankingLoss（用于回归或排序）
        - 配置学习率、batch size、max_length 等超参数
    - 实现训练 loop 或调用 CrossEncoder.fit()
- 训练与调试
    - 查看训练 / 验证集上的 loss 变化
    - 对比不同负样本策略的效果（随机负 vs hard negative）
    - 控制序列长度、batch size，避免 OOM
- 联合检索流程集成
    - 使用 Embedding 检索得到 top K 候选文档
    - 将 (query, doc) 对输入 Reranker，得到精排 score
    - 对比以下两种方案的效果：
        - 仅用 Embedding 检索
        - Embedding 检索 + Reranker 精排
    - 计算排序指标：Recall@K、MRR、nDCG 等
- 模型保存与在线推理
    - 保存微调后的 CrossEncoder 模型
    - 编写在线 Rerank 函数
        - 输入：query + 候选文档列表
        - 输出：按相关性得分排序后的文档列表
    - 给出与现有搜索 / 问答服务集成的伪代码示例（如两阶段检索：召回 + 精排）

### 4 Day 1 交付作业
#### 无 Python 基础组（任选其一）
- 提交可视化平台训练任务截图
- 包含模型选择
- LoRA 参数
- 训练结果/日志截图

#### Python 组（三选一）
##### ① LoRA 微调脚本

提交完整可运行的 LoRA 微调脚本（`.py` 或 `.ipynb`）
内容需要包含：

- 数据加载与处理
- LoRA 配置代码
- 模型微调训练脚本
- 附上训练日志或模型输出截图

##### ② Embedding 的微调
- Embedding 的训练数据、测试数据

##### ③ Reranker 的微调
- Reranker 的训练数据、测试数据

### 5 课后预期成果
- 掌握生成模型 + 检索模型的基础训练方法
- 完成至少一种 LoRA 或向量模型的微调