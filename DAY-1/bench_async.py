import asyncio
import httpx
import time
import os
from dotenv import load_dotenv
from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential
import matplotlib.pyplot as plt

load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

URLS = [
    "https://api.github.com/orgs/kubernetes",
    "https://api.github.com/orgs/prometheus",
    "https://api.github.com/orgs/grafana",
    "https://api.github.com/repos/langchain-ai/langgraph",
    "https://api.github.com/repos/microsoft/autogen",
    "https://api.github.com/users/torvalds",
    "https://api.github.com/users/gvanrossum",
    "https://api.github.com/repos/huggingface/transformers",
    "https://api.github.com/repos/openai/openai-python",
    "https://api.github.com/repos/tiangolo/fastapi",
] * 5


rate_limiter = AsyncLimiter(10, 1)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def fetch_async(client: httpx.AsyncClient, url: str):
    async with rate_limiter: # Respect rate limits
        start = time.perf_counter()
        try:
            resp = await client.get(url, timeout=10.0)
            elapsed = time.perf_counter() - start
            return url, resp.status_code, elapsed
        except Exception as e:
            elapsed = time.perf_counter() - start
            return url, f"ERR: {type(e).__name__}", elapsed

async def run_all_async():
 
    limits = httpx.Limits(max_connections=50, max_keepalive_connections=20)
    async with httpx.AsyncClient(headers=HEADERS, limits=limits, http2=True) as client:
        t0 = time.perf_counter()
        tasks = [fetch_async(client, url) for url in URLS]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        total = time.perf_counter() - t0
    return results, total

def plot_results(sync_total, async_total, async_times):
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))

  
    ax[0].bar(['Sync', 'Async'], [sync_total, async_total], color=['red', 'green'])
    ax[0].set_ylabel('Total Time (s)')
    ax[0].set_title(f'Speedup: {sync_total/async_total:.1f}x faster')

   
    ax[1].hist(async_times, bins=20, color='blue', alpha=0.7)
    ax[1].set_xlabel('Per-request latency (s)')
    ax[1].set_ylabel('Count')
    ax[1].set_title('Async Request Latency Distribution')

    plt.tight_layout()
    plt.savefig('latency_comparison.png')
    print("Saved chart to latency_comparison.png")

if __name__ == "__main__":
    
    SYNC_TOTAL_TIME = 28.5 # REPLACE with your actual sync result

    results, async_total = asyncio.run(run_all_async())
    async_times = [r[2] for r in results if isinstance(r[2], float)]

    print(f"\nASYNC: Total time for 50 requests: {async_total:.2f}s")
    print(f"ASYNC: Avg per request: {async_total/50:.3f}s")
    print(f"ASYNC: p99 latency: {sorted(async_times)[int(len(async_times)*0.99)]:.3f}s")
    print(f"\nSPEEDUP: {SYNC_TOTAL_TIME/async_total:.1f}x faster than sync")

    for url, status, elapsed in results[:5]:
        print(f"{status} {elapsed:.3f}s {url}")

    plot_results(SYNC_TOTAL_TIME, async_total, async_times)
