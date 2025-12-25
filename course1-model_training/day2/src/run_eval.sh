# # 评测微调前（base）
# python eval_law_vllm.py --mode base \
#   --model models/Qwen3-8B \
#   --closedbook output/law_opencompass_closedbook.jsonl \
#   --openbook output/law_opencompass_openbook.jsonl \
#   --out_dir eval_base \
#   --max_model_len 2048 --max_new_tokens 256 --gpu_mem_util 0.5

# # 评测微调后（lora）
# python eval_law_vllm.py --mode lora \
#   --model models/Qwen3-8B \
#   --lora_path LLaMA-Factory/saves/llama3-8b/lora/sft_r_8/checkpoint-411 \
#   --closedbook output/law_opencompass_closedbook.jsonl \
#   --openbook output/law_opencompass_openbook.jsonl \
#   --out_dir eval_lora \
#   --max_model_len 2048 --max_new_tokens 256 --gpu_mem_util 0.5


# 评测微调后（lora）
python eval_law_vllm.py --mode lora \
  --model models/Qwen3-8B \
  --lora_path LLaMA-Factory/saves/llama3-8b/lora/sft_r_16/checkpoint-411 \
  --closedbook output/law_opencompass_closedbook.jsonl \
  --openbook output/law_opencompass_openbook.jsonl \
  --out_dir eval_lora \
  --max_model_len 2048 --max_new_tokens 256 --gpu_mem_util 0.5
