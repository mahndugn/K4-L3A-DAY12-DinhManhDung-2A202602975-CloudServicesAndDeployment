"""Regression tests for CloudOps routing and API behavior, beyond the lab suite."""

import pytest

from utils.cloudops_knowledge import TOPICS, match_topic
from utils.mock_llm import ask_llm


@pytest.mark.parametrize("question,expected", [
    ("Docker image khác container thế nào?", "docker"),
    ("Docker multi-stage là gì?", "multi_stage"),
    ("Docker HEALTH check khác readiness thế nào?", "probes"),
    ("Redis dùng cho rate limit như thế nào?", "rate_limit"),
    ("Rate limit khác cost guard thế nào?", "budget"),
    ("Docker Compose dùng để làm gì?", "compose"),
    ("docker localhost redis connection refused", "network"),
    ("Redis volume dùng để làm gì?", "volume"),
    ("Docker layer cache là gì?", "cache"),
    ("Docker graceful shutdown SIGTERM", "shutdown"),
    ("cau hinh environment tren cloud", "config"),
    ("Redis giup scale agent ra sao?", "redis"),
    ("Deploy Docker lên Railway", "deployment"),
    ("Cloud la gi?", "cloud"),
])
def test_specific_question_selects_correct_topic(question, expected):
    assert match_topic(question).id == expected


@pytest.mark.parametrize("topic", TOPICS, ids=lambda topic: topic.id)
def test_catalog_examples_select_their_own_topic(topic):
    assert match_topic(topic.question).id == topic.id


def test_unrelated_words_do_not_match_port_or_auth_substrings():
    assert match_topic("sports author report") is None
    assert "chưa có câu trả lời" in ask_llm("Hôm nay ăn gì?")["answer"]


def test_followup_uses_latest_user_topic_without_topic_leak():
    history = [
        {"role": "user", "content": "Docker multi-stage là gì?"},
        {"role": "assistant", "content": "Redis is not the user's topic"},
        {"role": "user", "content": "Redis giúp scale ra sao?"},
    ]
    assert "Về Redis" in ask_llm("giai thich them", history)["answer"]
    assert "chưa có câu trả lời" in ask_llm("Hôm nay ăn gì?", history)["answer"]


def test_response_contract_and_repeatability():
    first = ask_llm("Docker là gì?")
    assert first == ask_llm("Docker là gì?")
    assert set(first) == {"answer", "tokens_in", "tokens_out", "cost_usd"}
    assert first["cost_usd"] > 0


def test_public_catalog_and_about(client):
    assert client.get("/").json()["mode"] == "offline-faq"
    assert len(client.get("/topics").json()["topics"]) == len(TOPICS)


def test_whitespace_question_is_rejected(client, auth_headers):
    response = client.post("/ask", headers=auth_headers, json={"question": "  \n  "})
    assert response.status_code == 422


def test_api_history_drives_followup(client_real_store, auth_headers):
    first = client_real_store.post("/ask", headers=auth_headers,
                                   json={"question": "Docker multi-stage là gì?"})
    assert first.status_code == 200
    second = client_real_store.post("/ask", headers=auth_headers,
                                    json={"question": "Giải thích thêm"})
    assert second.status_code == 200
    assert second.json()["history_length"] == 2
    assert "Về Docker multi-stage" in second.json()["answer"]


def test_unicode_invalid_key_returns_401(client):
    # Header bytes exercise the constant-time comparison without a str ASCII error.
    response = client.post("/ask", headers={b"X-API-Key": "khóa-sai".encode()},
                           json={"question": "Docker là gì?"})
    assert response.status_code == 401


def test_reinstall_signal_handler_does_not_recurse():
    import signal
    from app.lifecycle import Lifecycle

    originals = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
    calls = []
    try:
        signal.signal(signal.SIGTERM, lambda signum, frame: calls.append(signum))
        life = Lifecycle()
        life.install()
        life.install()
        life.request_shutdown(signal.SIGTERM, None)
        assert calls == [signal.SIGTERM]
    finally:
        for sig, handler in originals.items():
            signal.signal(sig, handler)
