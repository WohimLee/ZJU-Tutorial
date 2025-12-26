## 模型部署

### 1 安装 opencompass
- 官方 Github: https://github.com/open-compass/opencompass

```sh

conda create -n opencompass-vllm python=3.10
conda activate opencompass-vllm

git clone https://github.com/open-compass/opencompass opencompass
cd opencompass
pip install -e ".[vllm]"
```


### 2 部署模型
#### 2.1 本地部署推理
>Base 模型
```sh
python -m vllm.entrypoints.openai.api_server \
  --model models/Qwen3-8B \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.85 \
  --max-num-seqs 64 \
  --tensor-parallel-size 1 \
  --port 8000
```

>LoRA 模型
```sh
# LoRA SFT 微调后的模型
vllm serve /root/wohim/models/Qwen3-8B \
  --enable-lora \
  --lora-modules '{"name":"sft","path":"/root/wohim/LLaMA-Factory/saves/llama3-8b/lora/sft_r_16/checkpoint-411"}' \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.85 \
  --max-num-seqs 64
```

#### 2.2 公网部署推理

```sh
# 暴露到公网
python -m vllm.entrypoints.openai.api_server \
  --host 0.0.0.0 \
  --port 6666 \
  --model models/Qwen3-8B \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.85 \
  --max-num-seqs 64 \
  --tensor-parallel-size 1
```