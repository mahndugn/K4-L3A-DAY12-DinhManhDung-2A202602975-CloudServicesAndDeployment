"""Offline CloudOps adapter; tokens and USD are simulated lab measurements."""

from __future__ import annotations

from .cloudops_knowledge import answer_question

PRICE_INPUT_PER_1K = 0.00015
PRICE_OUTPUT_PER_1K = 0.00060


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def ask_llm(question: str, history: list[dict] | None = None) -> dict:
    """Keep the lab response contract; no external model or network is used."""
    history = history or []
    answer = answer_question(question, history)
    prompt_text = question + "".join(turn.get("content", "") for turn in history)
    tokens_in = _estimate_tokens(prompt_text)
    tokens_out = _estimate_tokens(answer)
    cost = (tokens_in * PRICE_INPUT_PER_1K + tokens_out * PRICE_OUTPUT_PER_1K) / 1000
    return {
        "answer": answer,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": round(cost, 8),
    }
