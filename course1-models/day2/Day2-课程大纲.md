## Day 2：模型部署与性能评估（课程大纲）
### 一、理论模块（Theory）
#### 1. 推理显存占用与性能影响因素

- 模型参数规模（parameter size）对显存的线性影响
- 量化方法（INT8 / INT4 / AWQ / GPTQ）如何降低显存与带来的性能折衷
- Batch size、sequence length 对显存、吞吐量的影响
- KV Cache 对大模型推理的意义
- CPU vs GPU 推理的差异与适用场景

#### 2. 常用任务评估指标（Evaluation Metrics）
##### 文本生成任务

- BLEU：n-gram 重叠度
- ROUGE：召回导向的摘要指标（ROUGE-L、ROUGE-1/2）
- 困惑度（PPL）：衡量语言模型的整体质量

##### 分类任务

- Accuracy：整体分类正确率
- Precision / Recall / F1：模型对少数类的表现
- 宏平均 / 微平均：不均衡数据集下的指标选择

#### 3. Benchmark 与测试集设计原则

- Benchmark 的定义与作用（可比性、稳定性、标准化）
- 如何构建 可靠、公平、无泄漏（no data leakage） 的测试集
- 样例数量、任务覆盖面、难度分布的设计
- 真实场景 vs 合成数据的平衡
- 如何避免过拟合 Benchmark（benchmark hacking）

### 二、案例演示（Live Demo）
#### 1. 微调模型的部署方式

- FastAPI 部署 REST API
- OpenAI-compatible API（如 vLLM / LM Studio / Ollama 风格）
- 本地部署 vs 服务器部署流程

#### 2. 原始模型 vs 微调模型 效果对比

- 采用相同 Prompt 输出示例进行主观对比
- 使用自动化指标（如 ROUGE、F1）进行客观评估
- 对比 inference latency / throughput

#### 3. 构建自动化评估 Pipeline
- 定义 Prompt + Test cases 输入规范
- 自动化执行任务：批量推理、多样本处理
- 结果保存与可视化（CSV/JSON → 表格/图形）

### 三、实操环节（Hands-on Lab）
#### 🔹 一般学员路径（Non-coders）

- 使用 vLLM 加速推理、体验动态 batch 优势
- 模型量化（INT8 / INT4）实际显存节省测试
- 使用 nvidia-smi / nvitop 观察 GPU 利用率、显存变化、吞吐情况

#### 🔹 Python 学员路径（Coders）
##### 需完成的脚本功能
- 模型加载与推理
    - 选择 vLLM 或 transformers
    - 设置显存限制、量化配置（如 bitsandbytes）
- 评测样例运行
    - 自动读取 test cases
    - 批量运行推理并记录输出
- 自动计算指标
    - 文本任务指标（BLEU/ROUGE/PPL）
    - 分类任务指标（Accuracy/F1 等）
- 推理性能分析
    - 计算平均延迟（latency）
    - 吞吐量（tokens/s 或 samples/s）
    - 显存占用记录与分析

### 四、Day 2 交付作业（Deliverable）

需提交一份 模型评估报告（PDF 或 Markdown），应包含以下内容：

#### 1. 模型性能对比

- 原始模型 vs 微调模型的文本输出示例
- 指标对比表（BLEU/ROUGE/F1 等）
- 定性分析（质量、风格、一致性）

#### 2. 推理速度与显存测试

- 使用 nvidia-smi 的截图或数据
- 延迟（latency）与吞吐量（throughput）测试结果表格
- 不同量化/Batch 的性能变化

#### 3. Benchmark 测试集设计说明

- 测试集来源（真实 vs 合成）
- 样例数量与任务覆盖
- 指标选择理由

#### 4. Python 学员需额外提交
- 推理脚本
- 评估脚本（含指标计算）
- 性能测试代码或日志