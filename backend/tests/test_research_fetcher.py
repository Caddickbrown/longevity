from unittest.mock import MagicMock, patch

import pytest

from backend.services.research_fetcher import FetchError, fetch_research, _search_pubmed, _fetch_pubmed_summaries

MOCK_SEARCH_RESPONSE = {
    "esearchresult": {"idlist": ["12345678", "87654321"]}
}

MOCK_SUMMARY_RESPONSE = {
    "result": {
        "12345678": {"title": "NMN extends healthspan in mice", "sortpubdate": "2025/01/01"},
        "87654321": {"title": "Rapamycin delays aging in mammals", "sortpubdate": "2024/12/01"},
    }
}


def _mock_get(url, **kwargs):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    if "esearch" in url:
        resp.json.return_value = MOCK_SEARCH_RESPONSE
    else:
        resp.json.return_value = MOCK_SUMMARY_RESPONSE
    return resp


def test_fetch_research_returns_articles():
    with patch("httpx.get", side_effect=_mock_get):
        articles = fetch_research(max_per_term=2)
    assert len(articles) > 0
    assert all("title" in a for a in articles)
    assert all("url" in a for a in articles)
    assert all(a["source"] == "pubmed" for a in articles)


def test_fetch_research_deduplicates():
    with patch("httpx.get", side_effect=_mock_get):
        articles = fetch_research(max_per_term=2)
    urls = [a["url"] for a in articles]
    assert len(urls) == len(set(urls))


def test_fetch_research_raises_on_all_failure():
    import httpx
    with patch("httpx.get", side_effect=httpx.HTTPError("timeout")):
        with pytest.raises(FetchError):
            fetch_research()


def test_search_pubmed_returns_empty_on_error():
    import httpx
    with patch("httpx.get", side_effect=httpx.HTTPError("timeout")):
        result = _search_pubmed("longevity")
    assert result == []


def test_fetch_pubmed_summaries_empty_input():
    result = _fetch_pubmed_summaries([])
    assert result == []
