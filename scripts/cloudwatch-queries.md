# ============================================================
# CloudWatch Logs Insights — Useful Queries
#
# Paste these into CloudWatch Logs Insights in the AWS Console.
# Select the relevant log group before running.
# ============================================================

#
# ── 1. Recent Errors ──────────────────────────────────────────
# Shows the last 50 errors across all Lambda functions.
#

fields @timestamp, level, message, exception
| filter level = "ERROR"
| sort @timestamp desc
| limit 50


#
# ── 2. Slow API Requests (> 5 seconds) ───────────────────────
# Useful for detecting cold starts or slow Gemini API calls.
#

fields @timestamp, @duration, @message
| filter @duration > 5000
| sort @duration desc
| limit 20


#
# ── 3. Task Processing Duration ──────────────────────────────
# Worker Lambda — how long each task takes.
#

fields @timestamp, message
| filter message like /Task .* completed/
| parse message "Processing task: * | payload: *" as task_name, payload
| stats count() as task_count, avg(@duration) as avg_ms, max(@duration) as max_ms by task_name


#
# ── 4. Cold Start Detection ─────────────────────────────────
# Lambda INIT_START events indicate a cold start.
#

fields @timestamp, @initDuration, @message
| filter @type = "REPORT" and @initDuration > 0
| stats count() as cold_starts,
        avg(@initDuration) as avg_init_ms,
        max(@initDuration) as max_init_ms
| sort cold_starts desc


#
# ── 5. Error Rate Over Time ──────────────────────────────────
# Error count per 5-minute bucket.
#

fields @timestamp
| filter level = "ERROR"
| stats count() as error_count by bin(5m)


#
# ── 6. SQS Dead Letter Queue Analysis ───────────────────────
# Find tasks that failed 3 times and ended up in the DLQ.
#

fields @timestamp, message
| filter message like /Task .* failed/
| parse message "Task * failed: *" as task_name, error
| stats count() as failures by task_name, error
| sort failures desc


#
# ── 7. Lambda Concurrent Executions ──────────────────────────
# Monitor how close we are to free tier limits.
#

fields @timestamp
| filter @type = "REPORT"
| stats count() as invocations by bin(1h)


#
# ── 8. Memory Usage ──────────────────────────────────────────
# Find Lambda invocations using the most memory.
#

fields @timestamp, @memorySize, @maxMemoryUsed
| filter @type = "REPORT"
| stats avg(@maxMemoryUsed/@memorySize * 100) as avg_pct_used,
        max(@maxMemoryUsed) as max_memory_mb
| sort avg_pct_used desc


#
# ── 9. Document Processing Pipeline ─────────────────────────
# Track document processing from upload to embedding.
#

fields @timestamp, message
| filter message like /file_id/
| sort @timestamp asc
| limit 100


#
# ── 10. Free Tier Budget Monitor ─────────────────────────────
# Estimate monthly Lambda GB-seconds usage.
#

fields @timestamp, @billedDuration, @memorySize
| filter @type = "REPORT"
| stats sum(@billedDuration / 1000 * @memorySize / 1024) as total_gb_seconds,
        count() as total_invocations
