"""Smoke test the local CloudOps service without printing credentials."""

from pathlib import Path
import os
import uuid

import httpx
from dotenv import load_dotenv


def main() -> None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    key = os.getenv("AGENT_API_KEY")
    if not key:
        raise SystemExit("Set AGENT_API_KEY in .env before running this demo.")
    headers = {"X-API-Key": key, "X-User-Id": f"cloudops-demo-{uuid.uuid4().hex[:12]}"}
    with httpx.Client(base_url="http://localhost:8000", timeout=15, trust_env=False) as client:
        for path in ("/health", "/ready", "/topics"):
            response = client.get(path)
            response.raise_for_status()
            print(f"GET {path}: {response.status_code}")
        denied = client.post("/ask", json={"question": "Docker là gì?"})
        if denied.status_code != 401:
            raise SystemExit(f"Expected 401 without key, got {denied.status_code}")
        for question in (
            "Docker multi-stage là gì?",
            "Readiness probe khác health check thế nào?",
            "Rate limit dùng Redis thế nào?",
            "Redis giúp scale agent ra sao?",
            "giai thich them",
        ):
            response = client.post("/ask", headers=headers, json={"question": question})
            response.raise_for_status()
            body = response.json()
            print(f"\n{question}\n{body['answer']}")
            print(f"history_length={body['history_length']}; simulated_cost_usd={body['cost_usd']}")


if __name__ == "__main__":
    main()
