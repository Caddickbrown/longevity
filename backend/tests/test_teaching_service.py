import json
from unittest.mock import MagicMock, patch

import pytest

from backend.models import Intervention
from backend.services.teaching import TeachingError, generate_explanation

MOCK_INTERVENTION = Intervention(
    id=1, name="Zone 2 Cardio", evidence_grade="A", cost_tier=1, tier=1,
    mechanism="Improves mitochondrial density and fat oxidation.", references="",
)

MOCK_RESPONSE = json.dumps({
    "explanation": "Zone 2 cardio works by training your aerobic base.",
    "why_it_matters": "Mitochondrial health is foundational to longevity.",
    "how_to_implement": "150+ min/week at 60-70% max HR.",
    "sources": [{"title": "Attia on Zone 2", "url": "https://peterattia.com/zone2"}],
    "difficulty": "moderate",
})


def _mock_client(api_key):
    client = MagicMock()
    msg = MagicMock()
    msg.content = [MagicMock(text=MOCK_RESPONSE)]
    client.messages.create.return_value = msg
    return client


def test_generate_explanation_returns_dict(monkeypatch):
    monkeypatch.setattr("backend.config.settings.anthropic_api_key", "sk-test")
    with patch("anthropic.Anthropic", side_effect=_mock_client):
        result = generate_explanation(MOCK_INTERVENTION)

    assert "explanation" in result
    assert "why_it_matters" in result
    assert "how_to_implement" in result
    assert isinstance(result["sources"], list)
    assert result["difficulty"] == "moderate"


def test_generate_explanation_raises_without_api_key(monkeypatch):
    monkeypatch.setattr("backend.config.settings.anthropic_api_key", "")
    with pytest.raises(TeachingError, match="ANTHROPIC_API_KEY"):
        generate_explanation(MOCK_INTERVENTION)


def test_generate_explanation_raises_on_invalid_json(monkeypatch):
    monkeypatch.setattr("backend.config.settings.anthropic_api_key", "sk-test")
    mock_client = MagicMock()
    mock_client.messages.create.return_value.content = [MagicMock(text="not json")]
    with patch("anthropic.Anthropic", return_value=mock_client):
        with pytest.raises(TeachingError, match="parse"):
            generate_explanation(MOCK_INTERVENTION)
