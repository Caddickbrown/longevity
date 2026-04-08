import json
from unittest.mock import MagicMock, patch

import pytest

from backend.services.research_synthesiser import SynthesisError, synthesise

SAMPLE_ARTICLES = [
    {"title": "NMN extends healthspan in mice", "snippet": "2025/01/01", "source": "pubmed"},
    {"title": "Rapamycin delays aging in mammals", "snippet": "2024/12/01", "source": "pubmed"},
]

SAMPLE_PROTOCOLS = ["NMN", "Sleep optimisation", "Zone 2 cardio"]

MOCK_CLAUDE_RESPONSE = json.dumps({
    "summary": "Recent research shows NMN is promising for NAD+ restoration.",
    "key_findings": ["NMN extends mouse lifespan", "Rapamycin inhibits mTOR"],
    "interventions_mentioned": ["NMN"],
    "evidence_updates": [{"protocol": "NMN", "finding": "Positive in animal models", "grade_change": "improved"}],
})


def _mock_anthropic_client(api_key):
    client = MagicMock()
    message = MagicMock()
    message.content = [MagicMock(text=MOCK_CLAUDE_RESPONSE)]
    client.messages.create.return_value = message
    return client


def test_synthesise_returns_digest(monkeypatch):
    monkeypatch.setattr("backend.config.settings.anthropic_api_key", "sk-test")
    with patch("anthropic.Anthropic", side_effect=_mock_anthropic_client):
        result = synthesise(SAMPLE_ARTICLES, SAMPLE_PROTOCOLS)

    assert result["source"] == "pubmed+claude"
    assert "NMN" in result["summary"]
    assert "NMN" in result["interventions_mentioned"]
    assert result["raw_response"] == MOCK_CLAUDE_RESPONSE


def test_synthesise_raises_without_api_key(monkeypatch):
    monkeypatch.setattr("backend.config.settings.anthropic_api_key", "")
    with pytest.raises(SynthesisError, match="ANTHROPIC_API_KEY"):
        synthesise(SAMPLE_ARTICLES, SAMPLE_PROTOCOLS)


def test_synthesise_raises_on_api_error(monkeypatch):
    import anthropic
    monkeypatch.setattr("backend.config.settings.anthropic_api_key", "sk-test")
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = anthropic.APIStatusError(
        "rate limit", response=MagicMock(status_code=429), body={}
    )
    with patch("anthropic.Anthropic", return_value=mock_client):
        with pytest.raises(SynthesisError):
            synthesise(SAMPLE_ARTICLES, SAMPLE_PROTOCOLS)


def test_synthesise_raises_on_invalid_json(monkeypatch):
    monkeypatch.setattr("backend.config.settings.anthropic_api_key", "sk-test")
    mock_client = MagicMock()
    message = MagicMock()
    message.content = [MagicMock(text="not valid json")]
    mock_client.messages.create.return_value = message
    with patch("anthropic.Anthropic", return_value=mock_client):
        with pytest.raises(SynthesisError, match="parse"):
            synthesise(SAMPLE_ARTICLES, SAMPLE_PROTOCOLS)
