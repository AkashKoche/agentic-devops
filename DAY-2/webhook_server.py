import hmac
import hashlib
import os
import json
from fastapi import FastAPI, Request, Header, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import arq
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import logging

load_dotenv()
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET").encode()
REDIS_SETTINGS = arq.connections.RedisSettings.from_dsn(os.getenv("REDIS_URL"))


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webhook")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await arq.create_pool(REDIS_SETTINGS)
    logger.info("ARQ Redis pool created")
    yield
    await app.state.redis.close()
    logger.info("ARQ Redis pool closed")

app = FastAPI(lifespan=lifespan)

def verify_signature(body: bytes, signature: str) -> bool:
    """GitHub HMAC SHA256 check. Without this, anyone can trigger your agents."""
    if not signature:
        return False
    hash_object = hmac.new(GITHUB_WEBHOOK_SECRET, msg=body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    return hmac.compare_digest(expected_signature, signature)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Webhook server is live!"}

@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None),
    x_github_delivery: str = Header(None),
):

    body = await request.body()
    if not verify_signature(body, x_hub_signature_256):
        logger.warning(f"Invalid signature for delivery {x_github_delivery}")
        raise HTTPException(status_code=403, detail="Invalid signature")


    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")


    incident_id = x_github_delivery
    logger.info(f"Received event={x_github_event} delivery={incident_id}")



    job = await app.state.redis.enqueue_job(
        "process_github_event",
        _job_id=incident_id,  
        event_type=x_github_event,
        payload=payload,
    )

    return JSONResponse(
        status_code=200,
        content={"status": "queued", "job_id": job.job_id, "incident_id": incident_id}
    )

@app.get("/healthz")
async def health():
    return {"status": "ok"}
