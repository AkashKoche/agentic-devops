import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("GITHU_TOKEN")
HEADERS= {"Authorization": f"Bearer {TOKEN}"}

URLS = [
    "https://api.github.com/orgs/kubernetes",
    "https://api.github.com/orgs/prometheus",
    "https://api.github.com/orgs/grafana",
    "https://api.github.com/repos/langchain-ai/langgraph",
    "https://api.github.com/repos/microsoft/autogen",
] * 10

def fetch_sync(url):
    start = time.perf_counter()
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        elapsed = time.perf_counter() - start
        return url, r.status_code, elapsed
    except Exception as e:
        return url, "ERR", time.perf_counter() - start

if __name__ == "__main__":
    t0 = time.perf_counter()
    results = [fetch_sync(url) for url in URLS[:50]]
    total = time.perf_counter() - t0

    print(f"SYNC: Total time for 50 requests: {total:.2f}s")
    print(f"SYNC: Avg per request: {total/50:.3f}s")
    for url, status, elapsed in results[:5]:
        print(f"{status} {elapsed:.3f}s {url}")
