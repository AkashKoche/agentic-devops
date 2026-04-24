# Day 1: Async Bedrock Lessons

## Numbers
- Sync 50 calls: 19.49s
- Async 50 calls: 4.33s
- Speedup: 6.5x
- p99 per-request: 0.086s

## What I’d Do Differently in Incident
1. Must use connection pooling - without it async was only 4x faster
2. Rate limiter is not optional - hit 403 immediately without it
3. Timeout + retry prevented 1 hung request from blocking all 49 others

## Next: Day 2 needs this client as a base for FastAPI webhook handler
