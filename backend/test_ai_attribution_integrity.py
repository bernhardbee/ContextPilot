"""Regression tests for provider/model attribution integrity in /ai/chat responses."""
from types import SimpleNamespace

from fastapi.testclient import TestClient

import main


def test_ai_chat_response_uses_executed_provider_and_model(monkeypatch):
    """API response must report executed provider/model, not merely requested values."""

    # Avoid expensive relevance/composer work and isolate attribution behavior.
    monkeypatch.setattr(main.relevance_engine, "rank_with_keywords", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        main.prompt_composer,
        "compose",
        lambda *args, **kwargs: SimpleNamespace(generated_prompt="prompt", original_task="task"),
    )

    executed_conversation = SimpleNamespace(
        id="conv-attr-1",
        provider="anthropic",
        model="claude-sonnet-4-5",
    )

    def fake_generate_response(**kwargs):
        # Simulate a divergence between requested and executed model/provider.
        return "actual assistant response", executed_conversation

    monkeypatch.setattr(main.ai_service, "generate_response", fake_generate_response)

    client = TestClient(main.app)
    response = client.post(
        "/ai/chat",
        json={
            "task": "test attribution",
            "max_context_units": 0,
            "provider": "ollama",
            "model": "llama3.2",
        },
    )

    assert response.status_code == 200
    payload = response.json()

    # Trust-critical contract: attribution reflects what actually executed.
    assert payload["provider"] == "anthropic"
    assert payload["model"] == "claude-sonnet-4-5"
