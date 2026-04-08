"""Generates plain-English teaching content for protocols via Claude."""
import json
import logging

from backend.config import settings
from backend.models import Intervention

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a longevity science educator. You explain evidence-based health interventions clearly, accurately, and without hype. You always cite real, verifiable sources."""

TEACHING_PROMPT = """Generate a teaching explanation for this longevity intervention:

Name: {name}
Evidence grade: {evidence_grade} (A=strong RCT evidence, B=moderate, C=emerging)
Mechanism summary: {mechanism}

Return valid JSON only with this exact structure:
{{
  "explanation": "2-3 paragraph plain-English explanation of how and why this works biologically",
  "why_it_matters": "1-2 paragraphs on its specific relevance to longevity and healthspan",
  "how_to_implement": "Practical, specific implementation guidance (doses, timing, frequency, what to watch for)",
  "sources": [
    {{"title": "source title", "url": "https://real-url.com"}},
    ...
  ],
  "difficulty": "easy|moderate|hard"
}}

Sources must be 3-5 real links — PubMed papers, Examine.com pages, Peter Attia articles, or similar reputable sources. Do not invent URLs."""


class TeachingError(Exception):
    pass


def generate_explanation(intervention: Intervention) -> dict:
    """
    Calls Claude to generate a teaching explanation for an intervention.
    Returns a dict matching ProtocolExplanation fields (minus intervention_id).
    Raises TeachingError if API key is missing or call fails.
    """
    if not settings.anthropic_api_key:
        raise TeachingError("ANTHROPIC_API_KEY not configured")

    import anthropic

    prompt = TEACHING_PROMPT.format(
        name=intervention.name,
        evidence_grade=intervention.evidence_grade,
        mechanism=intervention.mechanism,
    )

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        parsed = json.loads(raw)
    except anthropic.APIError as e:
        raise TeachingError(f"Claude API error: {e}") from e
    except (json.JSONDecodeError, IndexError) as e:
        raise TeachingError(f"Failed to parse Claude response: {e}") from e

    return {
        "explanation": parsed.get("explanation", ""),
        "why_it_matters": parsed.get("why_it_matters", ""),
        "how_to_implement": parsed.get("how_to_implement", ""),
        "sources": parsed.get("sources", []),
        "difficulty": parsed.get("difficulty", "moderate"),
    }
