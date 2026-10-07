"""Fetch complaints WITH narratives from the CFPB public API -> complaints.csv"""
import csv
import time

import httpx

URL = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
PRODUCTS = [
    "Debt collection",
    "Credit reporting or other personal consumer reports",
    "Mortgage",
    "Checking or savings account",
    "Credit card",
    "Student loan",
]
PER_PRODUCT = 700
PAGE = 100


def fetch(product):
    rows, frm = [], 0
    while len(rows) < PER_PRODUCT:
        params = {
            "product": product,
            "has_narrative": "true",
            "date_received_min": "2023-01-01",
            "size": PAGE,
            "frm": frm,
            "sort": "created_date_desc",
            "no_aggs": "true",
        }
        r = httpx.get(URL, params=params, timeout=60, follow_redirects=True)
        r.raise_for_status()
        data = r.json()
        hits = data["hits"]["hits"] if isinstance(data, dict) else data
        if not hits:
            break
        for h in hits:
            src = h.get("_source", h)
            text = (src.get("complaint_what_happened") or "").strip()
            if text:
                rows.append((product, text))
        frm += PAGE
        time.sleep(0.5)
    return rows[:PER_PRODUCT]


with open("complaints.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Product", "Consumer complaint narrative"])
    for p in PRODUCTS:
        got = fetch(p)
        print(p, len(got))
        w.writerows(got)