import json
from tqdm import tqdm

src_path = "DISC-Law-SFT-Triplet-released.jsonl"
alpaca_out = "law_alpaca.json"
sharegpt_out = "law_sharegpt.json"

alpaca_data = []
sharegpt_data = []

# 先统计总行数（用于显示百分比）
with open(src_path, "r", encoding="utf-8") as f:
    total_lines = sum(1 for _ in f)

with open(src_path, "r", encoding="utf-8") as f:
    for line in tqdm(f, total=total_lines, desc="Converting"):
        raw = json.loads(line)

        # ---------- 公共处理 ----------
        system_text = "\n".join(raw.get("reference", []))
        instruction = raw["input"]
        output = raw["output"]

        # ---------- Alpaca ----------
        alpaca_item = {
            "instruction": instruction,
            "input": "",
            "output": output,
            "system": system_text
        }
        alpaca_data.append(alpaca_item)

        # ---------- ShareGPT ----------
        sharegpt_item = {
            "conversations": [
                {"from": "human", "value": instruction},
                {"from": "gpt", "value": output}
            ],
            "system": system_text
        }
        sharegpt_data.append(sharegpt_item)

# 写文件
with open(alpaca_out, "w", encoding="utf-8") as f:
    json.dump(alpaca_data, f, ensure_ascii=False, indent=2)

with open(sharegpt_out, "w", encoding="utf-8") as f:
    json.dump(sharegpt_data, f, ensure_ascii=False, indent=2)

print("转换完成：")
print(f"- Alpaca -> {alpaca_out}")
print(f"- ShareGPT -> {sharegpt_out}")
