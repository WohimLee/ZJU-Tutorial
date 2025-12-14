## 🚀 大模型训练、微调与部署 — 3 天课程大纲（含可交付作业）
>📅 课时安排

- 3 天密集训练营，每天 9:00–12:00，14:00–17:00

### Day 1：大模型训练与微调基础
#### ✅ 理论模块

- 大模型训练流程（数据 → 训练 → 评估 → 部署）
- 迁移学习与参数高效微调（PEFT）
- LoRA/QLoRA 工作原理与适用场景
- 开源模型生态（LLaMA、Qwen）结构简介

#### ✅ 案例讲解

- 基于 Qwen3-8B 完成一个简单的文本分类或指令微调任务
- 对比：全参数训练 vs LoRA 微调的显存需求与效果差异

#### ✅ 实操环节
##### 🔹 无 Python 基础学员

- 使用可视化/低代码平台（如 ModelArts/魔塔/ModelScope Studio）
- 完成：上传数据 → 配置 LoRA 训练参数 → 启动训练任务

##### 🔹 有 Python 基础学员

使用 LlamaFactory、transformers、peft 手写微调脚本

内容包括：

- 数据集加载与预处理
- LoRA 配置
- 训练参数定义
- 启动训练与日志检查

#### 📌 Day1 交付作业（Deliverable）

任选一种：

>无 Python 基础组
- 提交可视化平台中配置好的训练任务截图（含参数与结果）。

>Python 组
- 提交一个可运行的 LoRA 微调脚本（.py 或 notebook）
- 包含：数据加载、LoRA 配置、训练启动代码
- 附上训练日志或模型输出截图

### Day 2：模型部署与性能评估
#### ✅ 理论模块

- 推理显存占用：影响因素（模型尺寸、量化、batch 等）
- 常用评估指标设计：
    - 文本生成任务：BLEU、ROUGE、困惑度（PPL）
    - 分类任务：Accuracy、F1、宏平均/微平均
- 什么是 Benchmark，如何设计可靠测试集

#### ✅ 案例演示

- 将 Day1 微调模型部署到本地/服务器（FastAPI 或 OpenAI-compatible API）
- 对比：原始模型 vs 微调模型的效果
- 构造自动化评估 pipeline（基于 prompt/test cases）

#### ✅ 实操环节
##### 🔹 一般学员
- 使用 vLLM 加速推理
- 体验量化（INT4/INT8）的效果
- 使用工具监控 GPU 利用率（如 nvidia-smi, grafana）

##### 🔹 Python 学员

编写脚本实现：
- 模型加载（vLLM 或 transformers）
- 评测样例运行
- 自动计算指标
- 分析推理吞吐量与延迟

#### 📌 Day2 交付作业（Deliverable）

提交一份 模型评估报告（PDF/Markdown），包含：

- 微调模型 vs 原始模型的性能对比（文本示例或指标）
- 推理速度/显存占用测试（截图或表格）
- Benchmark 测试集设计说明
- 若使用 Python，附带推理/评估脚本

### Day 3：综合实践 — 从数据到部署全流程项目
#### ✅ 全流程案例拆解

##### 1. 数据阶段

- 清洗业务数据、去重、分词/标注
- 构建训练数据集（Instruction / Conversation / Classification）
- 构建类别标签体系

##### 2. 训练阶段

- 按业务需求微调开源模型
- 训练监控（loss 曲线、过拟合分析）
- 模型效果验证（指标 & 人工测试）

##### 3. 部署阶段

- 使用 vLLM / FastAPI / Docker 部署服务
- 开放 RESTful API
- 配置日志与服务监控（QPS、延迟、错误率）

#### ✅ 实操环节

- 完成一个端到端迷你项目：
业务数据 → 训练数据集 → 微调 → 评估 → 部署 API → 测试服务

##### 🔹 Python 基础学员

全流程均需使用 Python 编写：
- 数据处理
- 训练脚本
- 推理/评估脚本
- 部署 API（FastAPI）
- 调用 API 完整示例

#### 📌 Day3 最终交付作业（Capstone Project Deliverable）

提交一个“可运行的端到端项目包”（zip 或 GitHub repo），需包含：

- 数据处理脚本（data_clean.py）
- 训练脚本（train_lora.py / notebook）
- 评估脚本（evaluate.py）
- 部署服务脚本（api_server.py — vLLM 或 FastAPI）
- 说明文档 README.md
    - 数据说明
    - 训练参数与设备
    - 模型表现
    - 部署方式
    - API 调用示例

可选加分项：提供 Dockerfile 或在线 demo。

### 🎯 课程总体交付成果（学员最终能完成）

在 3 天课程结束后，每位学员将能够：

- 完成一次 LoRA 微调
- 对模型进行基准测试与性能评估
- 将模型部署成可调用 API 服务
- 独立产出一个完整的端到端落地项目