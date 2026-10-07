"""Sample the CFPB complaints CSV into train/test files.

Usage:
  python scripts/prepare_data.py path/to/complaints.csv [--top-n 6] [--cap 500] [--test-size 300]

Writes data/categories.json, data/train.csv, data/test.csv,
data/urgency_label_sample.csv (50 test rows for you to hand-label).
"""
import argparse
import json
import os

import pandas as pd
from sklearn.model_selection import train_test_split

PRODUCT_COL = "Product"
TEXT_COL = "Consumer complaint narrative"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--top-n", type=int, default=6)
    ap.add_argument("--cap", type=int, default=500, help="max rows kept per product")
    ap.add_argument("--test-size", type=int, default=300)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    parts = []
    for chunk in pd.read_csv(args.csv, usecols=[PRODUCT_COL, TEXT_COL], chunksize=200_000):
        chunk = chunk.dropna(subset=[TEXT_COL])
        parts.append(chunk.sample(frac=0.1, random_state=args.seed))
    df = pd.concat(parts, ignore_index=True)
    df.columns = ["product", "text"]
    df = df[df["text"].str.len() > 50]

    top = df["product"].value_counts().head(args.top_n).index.tolist()
    df = df[df["product"].isin(top)]
    df = pd.concat(
        [
            df[df["product"] == p].sample(min((df["product"] == p).sum(), args.cap), random_state=args.seed)
            for p in top
        ],
        ignore_index=True,
    )

    train, test = train_test_split(
        df, test_size=args.test_size, stratify=df["product"], random_state=args.seed
    )
    test = test.reset_index(drop=True)
    test.insert(0, "row_id", test.index)

    os.makedirs("data", exist_ok=True)
    with open("data/categories.json", "w", encoding="utf-8") as f:
        json.dump(sorted(top), f, indent=2)
    train.to_csv("data/train.csv", index=False)
    test.to_csv("data/test.csv", index=False)
    sample = test.head(50)[["row_id", "text"]].copy()
    sample["urgent_label"] = ""  # fill with 1 (urgent) or 0 (not urgent) by hand
    sample.to_csv("data/urgency_label_sample.csv", index=False)

    print("categories:", sorted(top))
    print("train rows:", len(train), "| test rows:", len(test))
    print("per-product counts in test:\n", test["product"].value_counts().to_string())


if __name__ == "__main__":
    main()
