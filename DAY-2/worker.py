import asyncio
import arq
from typing import Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

# This function name MUST match what you enqueue in webhook_server.py
async def process_github_event(ctx: dict, event_type: str, payload: dict) -> Any:
    """
    This is Day 3's job: turn this into the agent entry point.
    For Day 2, we just prove the queue works and log what we got.
    """
    incident_id = ctx['job_id'] # arq passes job_id in ctx
    logger.info(f"[{incident_id}] Worker picked up event: {event_type}")

    if event_type == "push":
        repo = payload['repository']['full_name']
        pusher = payload['pusher']['name']
        commit = payload['head_commit']['id'][:7]
        logger.info(f"[{incident_id}] Push to {repo} by {pusher}, commit {commit}")
        # Day 10: if commit_msg contains 'fix', trigger eval suite

    elif event_type == "workflow_run" and payload['action'] == 'completed':
        if payload['workflow_run']['conclusion'] == 'failure':
            logger.warning(f"[{incident_id}] CI FAILED: {payload['workflow_run']['html_url']}")
            # Day 41: this is where Self-Healing CI agent starts

    # Simulate work. In real agent, this is where you call Day 1's async http client.
    await asyncio.sleep(0.1)
    return {"status": "processed", "incident_id": incident_id}

# arq worker settings
async def startup(ctx):
    logger.info("Worker starting up")

async def shutdown(ctx):
    logger.info("Worker shutting down")

class WorkerSettings:
    functions = [process_github_event]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = arq.connections.RedisSettings.from_dsn("redis://localhost:6379/0")
    max_jobs = 10 # Parallelism. Tune this. 10 means 10 incidents at once.
