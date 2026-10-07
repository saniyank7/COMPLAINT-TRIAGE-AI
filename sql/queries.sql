-- Run against triage.db (sqlite3 triage.db < sql/queries.sql)

-- Complaints per product
SELECT product, COUNT(*) AS n FROM triage_results WHERE product IS NOT NULL GROUP BY product ORDER BY n DESC;

-- Urgent complaints per day
SELECT DATE(created_at) AS day, COUNT(*) AS urgent_n FROM triage_results WHERE urgent = 1 GROUP BY day ORDER BY day;

-- Latency and token cost
SELECT ROUND(AVG(latency_ms)) AS avg_latency_ms, MAX(latency_ms) AS max_latency_ms,
       ROUND(AVG(prompt_tokens + completion_tokens), 1) AS avg_tokens FROM triage_results;

-- Reliability: first-try valid JSON rate and final failures
SELECT ROUND(AVG(valid_json), 3) AS first_try_valid_rate,
       SUM(CASE WHEN product IS NULL THEN 1 ELSE 0 END) AS final_failures FROM triage_results;

-- Most common failure reasons
SELECT error, COUNT(*) AS n FROM triage_results WHERE error != '' GROUP BY error ORDER BY n DESC LIMIT 10;
