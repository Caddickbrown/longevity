"""Uses Claude to synthesise fetched research into a structured digest."""
import json
import logging
from typing import Any

from backend.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a longevity research analyst. You receive a list of recent scientific paper titles and metadata, plus the user's active intervention protocols. Your job is to synthesise this into a clear, actionable digest.

Respond with valid JSON only — no markdown, no prose outside the JSON object."""

DIGEST_PROMPT = """Here are recent papers from PubMed on longevity-related topics:

{articles}

The user's active protocols are:
{protocols}

Produce a JSON digest with this exact structure:
{{
  "summary": "2-3 paragraph plain-English summary of the most relevant findings",
  "key_findings": ["finding 1", "finding 2", ...],
  "interventions_mentioned": ["exact protocol names from the user's list that are relevant"],
  "evidence_updates": [
    {{"protocol": "name", "finding": "what the new research says", "grade_change": "improved|unchanged|weakened"}}
  ]
}}"""


class SynthesisError(Exception):
    pass


def synthesise(articles: list[dict[str, Any]], active_protocols: list[str]) -> dict[str, Any]:
    """
    Calls Claude to synthesise research articles into a digest.
    Returns a dict matching ResearchDigest fields.
    Raises SynthesisError if the API key is missing or the call fails.
    """
    if not settings.anthropic_api_key:
        raise SynthesisError("ANTHROPIC_API_KEY not configured")

    import anthropic

    article_text = "\n".join(
        f"- {a['title']} ({a['source']}, {a.get('snippet', '')})" for a in articles[:30]
    )
    protocol_text = "\n".join(f"- {p}" for p in active_protocols) or "None specified"

    prompt = DIGEST_PROMPT.format(articles=article_text, protocols=protocol_text)

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
        raise SynthesisError(f"Claude API error: {e}") from e
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        raise SynthesisError(f"Failed to parse Claude response: {e}") from e

    return {
        "source": "pubmed+claude",
        "summary": parsed.get("summary", ""),
        "interventions_mentioned": parsed.get("interventions_mentioned", []),
        "raw_response": raw,
    }
