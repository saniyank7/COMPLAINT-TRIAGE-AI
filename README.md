# COMPLAINT-TRIAGE-AI
# Complaint Triage Service

An LLM-powered service that reads a customer complaint and returns a structured triage result
(product category, issue, one-line summary, urgency flag), with an evaluation against a
classical ML baseline.

## 1. Problem statement

A bank receives thousands of customer complaints through email, app and branches. Staff must read
each one, decide which product it concerns, summarise it, and spot urgent cases (fraud, legal or
regulatory threats, severe hardship) so they reach the right team quickly. Done by hand this is slow
and inconsistent, and urgent cases can sit in a queue.

**Goal:** build a small, tested, containerised service that automates first-line triage, and measure
honestly how well it works compared with a simple baseline, including latency, cost and reliability.

**Data:** the public CFPB Consumer Complaint Database (US data; the problem is the same for Indian
banks). Only complaints with a consumer narrative are used.

## 2. Expected output (what "done" looks like)

1. **A running API**
   - `POST /triage` with `{"text": "..."}` returns:
     ```json
     {"product": "Mortgage", "issue": "Payment not credited", "summary": "Customer says a payment was not applied to the loan.", "urgent": false, "urgency_reason": "", "latency_ms": 1200}
     ```
   - `GET /health`, `GET /stats` (request count, avg latency, first-try valid-JSON rate, failures).
2. **A database** (`triage.db`) with every request logged, plus `sql/queries.sql` for reporting.
3. **An evaluation** (`results/eval_results.json`) on 300 held-out complaints:

   | Metric | Baseline (TF-IDF + LR) | LLM |
   |---|---|---|
   | Product accuracy | from `baseline.py` | from `run_eval.py` |
   | First-try valid JSON rate | n/a | from `run_eval.py` |
   | Median latency / tokens per call | n/a | from `run_eval.py` |
   | Urgency agreement with your hand labels (50 rows) | n/a | from `run_eval.py` |

4. **Engineering hygiene:** pytest tests passing, Dockerfile, GitHub Actions running tests on push,
   secrets only in `.env` (never committed).
5. **A short write-up** in this README: results, what failed, trade-offs.

## 3. Step-by-step procedure

### Step 0: Setup (20 min)
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env     # then fill LLM_API_KEY, LLM_BASE_URL, LLM_MODEL (see comments in the file)
python -m pytest -q      # should pass before you touch anything
git init && git add . && git commit -m "scaffold"
```
Get a free API key (Groq or Gemini) or run Ollama locally. Check the provider docs for current model names.

### Step 1: Get and sample the data (30 min)
Download the complaints CSV from consumerfinance.gov (Consumer Complaint Database → export CSV).
```bash
python scripts/prepare_data.py path/to/complaints.csv
```
Check the printed category list and counts. If a column name error appears, the CSV layout changed:
edit `PRODUCT_COL` / `TEXT_COL` at the top of the script. Note: the test set is balanced across
products, so accuracy here is not the same as accuracy on the real mix. Say so in your write-up.

### Step 2: Baseline (30 min)
```bash
python scripts/baseline.py
```
Records `results/baseline_metrics.json`. This is the number the LLM must be compared against.

### Step 3: Try the LLM on a few complaints (1 hr)
```bash
uvicorn app.main:app --reload
curl -X POST localhost:8000/triage -H "Content-Type: application/json" -d '{"text": "Paste a real complaint here ..."}'
```
Fix the prompt in `app/llm.py` if outputs are poor. Then run `python scripts/run_eval.py --limit 20` to
check the loop works end to end before spending your rate limit on all 300.

### Step 4: Full evaluation (1-2 hrs, mostly waiting)
```bash
python scripts/run_eval.py
```
Results are cached, so an interrupted run resumes and re-runs are free. Meanwhile, hand-label the 50
rows in `data/urgency_label_sample.csv` (fill `urgent_label` with 1 or 0) and re-run `run_eval.py`
to get urgency agreement. Label before looking at the model's answers.

### Step 5: SQL and observability (30 min)
```bash
sqlite3 triage.db < sql/queries.sql
```
Use the real API (Step 3) for some requests so the table has data. Screenshot or paste a couple of results into the README.

### Step 6: Tests, Docker, CI (1 hr)
```bash
python -m pytest -q
docker build -t triage . && docker run --env-file .env -p 8000:8000 triage
```
Push to GitHub; the workflow in `.github/workflows/tests.yml` runs tests automatically.

### Step 7: Deploy and get users (1-2 hrs)
Deploy the container to Azure (App Service / Container Apps) if you have access, otherwise Render.
Set the env vars in the platform's secret settings. Have 5-10 people try it and note what broke.

### Step 8: Write-up (30 min)
Fill in the results table with your real numbers. Add: 3 failure examples, what you changed in the
prompt and what effect it had, latency/cost trade-offs, and limitations (US data, balanced test set,
small hand-labeled urgency set, no personal data should be sent).

## 4. Resume bullet (fill in only from your own results)

> Built a complaint-triage service (FastAPI, SQL, LLM with structured JSON output, Docker, GitHub
> Actions) on [N] public CFPB complaints; compared against a TF-IDF baseline on [N] held-out
> complaints ([X]% vs [Y]% product accuracy), with [Z]% valid-JSON rate on the first try and
> [W] s median latency.

## 5. Interview talking points
- Why compare with a baseline, and what the LLM added beyond accuracy (summaries, urgency).
- How you handled invalid JSON (validate, retry once, log, return 422).
- Quality / latency / cost trade-off from your logged numbers.
- Privacy: public data only, redacted text, no personal data sent, keys in env vars.
- What you would do next: retrieval of policy text, a larger labeled urgency set, drift monitoring.
