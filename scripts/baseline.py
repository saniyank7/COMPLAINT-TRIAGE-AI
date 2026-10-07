"""TF-IDF + logistic regression baseline for product classification."""
import json
import os

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import make_pipeline


def main():
    train = pd.read_csv("data/train.csv")
    test = pd.read_csv("data/test.csv")
    model = make_pipeline(
        TfidfVectorizer(max_features=50000, ngram_range=(1, 2), sublinear_tf=True, stop_words="english"),
        LogisticRegression(max_iter=1000),
    )
    model.fit(train["text"], train["product"])
    pred = model.predict(test["text"])
    metrics = {
        "n_train": len(train),
        "n_test": len(test),
        "accuracy": round(float(accuracy_score(test["product"], pred)), 4),
        "macro_f1": round(float(f1_score(test["product"], pred, average="macro")), 4),
    }
    os.makedirs("results", exist_ok=True)
    with open("results/baseline_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(metrics)


if __name__ == "__main__":
    main()
