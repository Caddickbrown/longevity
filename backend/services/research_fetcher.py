"""Fetches raw research content from PubMed and curated longevity sources."""
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PUBMED_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

SEARCH_TERMS = [
    "longevity aging intervention",
    "HRV heart rate variability training",
    "VO2max exercise longevity",
    "sleep quality health outcomes",
    "NMN NR NAD+ supplementation human",
    "rapamycin mTOR longevity",
    "senolytics dasatinib quercetin",
    "creatine supplementation benefits",
    "omega-3 cardiovascular longevity",
    "time restricted eating fasting longevity",
]


class FetchError(Exception):
    pass


def _search_pubmed(term: str, max_results: int = 3) -> list[str]:
    """Returns a list of PubMed IDs for a search term."""
    try:
        resp = httpx.get(
            PUBMED_SEARCH_URL,
            params={"db": "pubmed", "term": term, "retmax": max_results, "retmode": "json", "sort": "relevance"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("esearchresult", {}).get("idlist", [])
    except httpx.HTTPError as e:
        logger.warning("PubMed search failed for '%s': %s", term, e)
        return []


def _fetch_pubmed_summaries(pmids: list[str]) -> list[dict[str, Any]]:
    """Returns title + abstract snippets for a list of PubMed IDs."""
    if not pmids:
        return []
    try:
        resp = httpx.get(
            PUBMED_SUMMARY_URL,
            params={"db": "pubmed", "id": ",".join(pmids), "retmode": "json"},
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json().get("result", {})
        articles = []
        for pmid in pmids:
            doc = result.get(pmid, {})
            title = doc.get("title", "")
            if title:
                articles.append({
                    "title": title,
                    "snippet": doc.get("sortpubdate", ""),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "source": "pubmed",
                })
        return articles
    except httpx.HTTPError as e:
        logger.warning("PubMed fetch failed for %s: %s", pmids, e)
        return []


def fetch_research(max_per_term: int = 3) -> list[dict[str, Any]]:
    """
    Fetches recent longevity research from PubMed.
    Returns list of {title, snippet, url, source} dicts.
    Raises FetchError if all sources fail.
    """
    articles: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for term in SEARCH_TERMS:
        pmids = _search_pubmed(term, max_results=max_per_term)
        for article in _fetch_pubmed_summaries(pmids):
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                articles.append(article)

    if not articles:
        raise FetchError("No research articles fetched — PubMed may be unreachable")

    logger.info("Fetched %d unique research articles", len(articles))
    return articles
