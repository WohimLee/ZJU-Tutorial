import argparse
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest


# -----------------------------
# IO
# -----------------------------
def read_jsonl(path: str) -> List[Dict[str, Any]]:
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def safe_str(x: Any) -> str:
    return "" if x is None else str(x)


# -----------------------------
# Scoring (rule-based)
# -----------------------------
ARTICLE_PAT = re.compile(r"第([0-9一二三四五六七八九十百千两〇零]+)条")
OVER_SPEC_PAT = re.compile(r"(\d+)\s*年|(\d+)\s*个月|(\d+)\s*月")


def normalize_article(a: str) -> str:
    a = (a or "").strip()
    m = re.search(r"(第[0-9一二三四五六七八九十百千两〇零]+条)", a)
    return m.group(1) if m else a


@dataclass
class Metrics:
    n: int = 0
    crime_hit: int = 0
    law_hit: int = 0
    range_hit: int = 0
    range_applicable: int = 0
    over_spec: int = 0
    hallucinated_article: int = 0

    def to_dict(self) -> Dict[str, Any]:
        def rate(x: int, d: int) -> float:
            return 0.0 if d == 0 else x / d

        return {
            "n": self.n,
            "crime_hit_rate": rate(self.crime_hit, self.n),
            "law_hit_rate": rate(self.law_hit, self.n),
            "range_hit_rate": (None if self.range_applicable == 0 else rate(self.range_hit, self.range_applicable)),
            "range_applicable": self.range_applicable,
            "over_spec_rate": rate(self.over_spec, self.n),
            "hallucinated_article_rate": rate(self.hallucinated_article, self.n),
        }


def score_one(pred: str, ref: Dict[str, Any]) -> Dict[str, Any]:
    pred = safe_str(pred)
    ref = ref or {}

    ref_crime = safe_str(ref.get("crime")).strip()
    ref_articles = ref.get("law_articles") or []
    ref_articles_norm = {normalize_article(a) for a in ref_articles if a}
    ref_range = ref.get("sentence_range")
    ref_range = None if ref_range in (None, "", "null") else str(ref_range).strip()

    crime_hit = bool(ref_crime) and (ref_crime in pred)

    law_hit = False
    for a in ref_articles_norm:
        if a and a in pred:
            law_hit = True
            break
    if not law_hit:
        for a in ref_articles:
            if a and str(a) in pred:
                law_hit = True
                break

    range_hit: Optional[bool] = None
    if ref_range:
        range_hit = (ref_range in pred)

    over_spec = bool(OVER_SPEC_PAT.search(pred))

    pred_articles = {f"第{m.group(1)}条" for m in ARTICLE_PAT.finditer(pred)}
    hallucinated_article = False
    if pred_articles and ref_articles_norm:
        hallucinated_article = any(a not in ref_articles_norm for a in pred_articles)

    return {
        "crime_hit": crime_hit,
        "law_hit": law_hit,
        "range_hit": range_hit,
        "over_spec": over_spec,
        "hallucinated_article": hallucinated_article,
    }


def aggregate(metrics: Metrics, one: Dict[str, Any], ref: Dict[str, Any]) -> None:
    metrics.n += 1
    if one["crime_hit"]:
        metrics.crime_hit += 1
    if one["law_hit"]:
        metrics.law_hit += 1
    if one["over_spec"]:
        metrics.over_spec += 1
    if one["hallucinated_article"]:
        metrics.hallucinated_article += 1
    if ref.get("sentence_range"):
        metrics.range_applicable += 1
        if one["range_hit"] is True:
            metrics.range_hit += 1


# -----------------------------
# Inference
# -----------------------------
def build_llm(model_path: str, max_model_len: int, gpu_mem_util: float, lora_path: Optional[str]) -> Tuple[LLM, Optional[LoRARequest]]:
    if lora_path:
        llm = LLM(
            model=model_path,
            trust_remote_code=True,
            enable_lora=True,
            max_model_len=max_model_len,
            gpu_memory_utilization=gpu_mem_util,
        )
        lora_req = LoRARequest("sft_adapter", 1, lora_path)
        return llm, lora_req

    llm = LLM(
        model=model_path,
        trust_remote_code=True,
        max_model_len=max_model_len,
        gpu_memory_utilization=gpu_mem_util,
    )
    return llm, None


def generate_once(llm: LLM, prompts: List[str], sampling: SamplingParams, lora_req: Optional[LoRARequest]) -> List[str]:
    # ✅ 一次性 generate，避免刷屏/重复 tqdm
    outs = llm.generate(prompts, sampling_params=sampling, lora_request=lora_req)
    preds: List[str] = []
    for o in outs:
        preds.append(o.outputs[0].text if o.outputs else "")
    return preds


# -----------------------------
# Main
# -----------------------------
def eval_file(name: str, path: str, llm: LLM, lora_req: Optional[LoRARequest], sampling: SamplingParams, out_dir: str) -> None:
    rows = read_jsonl(path)
    prompts = [r["question"] for r in rows]
    refs = [r.get("reference", {}) for r in rows]
    ids = [r.get("id", str(i)) for i, r in enumerate(rows)]

    preds = generate_once(llm, prompts, sampling, lora_req)

    m = Metrics()
    out_rows: List[Dict[str, Any]] = []
    for rid, q, ref, pred in zip(ids, prompts, refs, preds):
        s = score_one(pred, ref)
        aggregate(m, s, ref)
        out_rows.append({
            "id": rid,
            "dataset": name,
            "question": q,
            "reference": ref,
            "prediction": pred,
            "score": s,
        })

    os.makedirs(out_dir, exist_ok=True)
    write_jsonl(os.path.join(out_dir, f"{name}.pred.jsonl"), out_rows)

    print("\n" + "=" * 80)
    print(f"DATASET: {name}")
    print(f"PATH: {path}")
    for k, v in m.to_dict().items():
        print(f"  {k}: {v}")
    print(f"Saved: {os.path.join(out_dir, f'{name}.pred.jsonl')}")
    print("=" * 80)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["base", "lora"], required=True, help="base=微调前；lora=微调后(LoRA)")
    ap.add_argument("--model", default="models/Qwen3-8B")
    ap.add_argument("--lora_path", default="LLaMA-Factory/saves/llama3-8b/lora/sft")
    ap.add_argument("--openbook", default="output/law_opencompass_openbook.jsonl")
    ap.add_argument("--closedbook", default="output/law_opencompass_closedbook.jsonl")
    ap.add_argument("--out_dir", default="eval_outputs_law_one")
    ap.add_argument("--max_new_tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top_p", type=float, default=1.0)
    ap.add_argument("--max_model_len", type=int, default=2048)
    ap.add_argument("--gpu_mem_util", type=float, default=0.50)
    args = ap.parse_args()

    lora_path = args.lora_path if args.mode == "lora" else None

    sampling = SamplingParams(
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_new_tokens,
    )

    print(f"[INFO] mode={args.mode} model={args.model} lora_path={lora_path}")
    llm, lora_req = build_llm(args.model, args.max_model_len, args.gpu_mem_util, lora_path)

    if os.path.exists(args.closedbook):
        eval_file("law_closedbook", args.closedbook, llm, lora_req, sampling, args.out_dir)
    else:
        print(f"[WARN] closedbook not found: {args.closedbook}")

    if os.path.exists(args.openbook):
        eval_file("law_openbook", args.openbook, llm, lora_req, sampling, args.out_dir)
    else:
        print(f"[WARN] openbook not found: {args.openbook}")


if __name__ == "__main__":
    main()
