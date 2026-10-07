"""Run the LLM triage on data/test.csv and compare with the baseline.

Results are cached in results/cache.jsonl so re-runs are free and an
interrupted run can resume. Use --limit 20 first to check it works.

Usage: python scripts/run_eval.py [--limit N] [--sleep 2.0]
"""
import argparse
import json
import os
import statistics
import time

import pandas as pd

from app.llm import run_triage

CACHE = "results/cache.jsonl"


def load_cache() -> dict:
    cache = {}
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                cache[rec["row_id"]] = rec
    return cache


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--sleep", type=float, default=2.0, help="seconds between calls (rate limits)")
    args = ap.parse_args()

    test = pd.read_csv("data/test.csv")
    if args.limit:
        test = test.head(args.limit)
    os.makedirs("results", exist_ok=True)
    cache = load_cache()

    with open(CACHE, "a", encoding="utf-8") as out:
        for _, row in test.iterrows():
            rid = int(row["row_id"])
            if rid in cache:
                continue
            try:
                result, meta = run_triage(row["text"])
            except Exception as e:
                print(f"row {rid}: provider error {type(e).__name__}; stopping, re-run to resume")
                break
            rec = {
                "row_id": rid,
                "true_product": row["product"],
                "pred_product": result.product if result else None,
                "urgent": result.urgent if result else None,
                **meta,
            }
            cache[rid] = rec
            out.write(json.dumps(rec) + "\n")
            out.flush()
            time.sleep(args.sleep)

    recs = [cache[int(r)] for r in test["row_id"] if int(r) in cache]
    n = len(recs)
    if n == 0:
        print("No results yet.")
        return
    correct = sum(1 for r in recs if r["pred_product"] == r["true_product"])
    metrics = {
        "n_evaluated": n,
        "llm_accuracy": round(correct / n, 4),  # failures count as wrong
        "first_try_valid_json_rate": round(sum(1 for r in recs if r["valid_json"]) / n, 4),
        "final_failure_rate": round(sum(1 for r in recs if r["pred_product"] is None) / n, 4),
        "median_latency_ms": int(statistics.median(r["latency_ms"] for r in recs)),
        "avg_tokens_per_call": round(sum(r["prompt_tokens"] + r["completion_tokens"] for r in recs) / n, 1),
    }

    # optional: urgency agreement with your hand labels
    if os.path.exists("data/urgency_label_sample.csv"):
        lab = pd.read_csv("data/urgency_label_sample.csv").dropna(subset=["urgent_label"])
        pairs = [
            (int(l) == 1, cache[int(r)]["urgent"])
            for r, l in zip(lab["row_id"], lab["urgent_label"])
            if int(r) in cache and cache[int(r)]["urgent"] is not None
        ]
        if pairs:
            metrics["urgency_n_labeled"] = len(pairs)
            metrics["urgency_agreement"] = round(sum(1 for a, b in pairs if a == b) / len(pairs), 4)

    if os.path.exists("results/baseline_metrics.json"):
        with open("results/baseline_metrics.json") as f:
            metrics["baseline_accuracy"] = json.load(f)["accuracy"]

    with open("results/eval_results.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
