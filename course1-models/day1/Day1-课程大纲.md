## 课程大纲：Day 1 —— 大模型训练、微调基础
>课程目标

- 理解大模型训练全流程、PEFT、LoRA/QLoRA
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



### 2. 案例讲解（Case Study）

#### 1 全参 identity 微调
- 基于 Qwen3-0.6B
#### 2 LoRA 微调案例
- 基于 Qwen3-8B 做分类或指令微调。


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


### 4 Day 1 交付作业
#### 无 Python 基础组（任选其一）
- 提交可视化平台训练任务截图
- 包含模型选择
- LoRA 参数
- 训练结果/日志截图

#### Python 组
##### ① identity 训练脚本

##### ② LoRA 微调脚本



### 5 课后预期成果
- 掌握生成模型 + 检索模型的基础训练方法
- 完成至少一种 LoRA 或向量模型的微调