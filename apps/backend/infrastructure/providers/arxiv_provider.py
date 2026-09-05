"""
DeepFeed AI - arXiv Source Provider (M6)
Discovers research papers from arXiv using their Atom API.
Trust score: 0.95 (highest credibility as per TDS §12.6)
"""
import uuid
import httpx
from datetime import datetime, timezone
from typing import Optional, List
from xml.etree import ElementTree as ET
from domain.interfaces.source_provider import SourceProvider, ContentCandidate
from logger import get_logger

logger = get_logger(__name__)

# arXiv now permanently redirects http:// to https:// (301). httpx doesn't
# follow redirects by default, so every request here used to come back as a
# 301 and get raise_for_status()'d into an "arxiv_query_failed" — silently
# and permanently breaking arXiv discovery (the single highest-trust source,
# per seed.py) for every query, for every user. Using https directly avoids
# the redirect round-trip entirely rather than just tolerating it.
ARXIV_API_BASE = "https://export.arxiv.org/api/query"
ARXIV_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS2 = "http://arxiv.org/schemas/atom"


class ArXivProvider(SourceProvider):
    """Discovers research papers from arXiv."""

    @property
    def provider_name(self) -> str:
        return "arxiv"

    async def discover(
        self,
        source_id: uuid.UUID,
        base_url: str,
        search_queries: Optional[List[str]] = None,
        max_items: int = 20,
    ) -> List[ContentCandidate]:
        queries = search_queries or ["machine learning", "artificial intelligence"]
        candidates: List[ContentCandidate] = []

        for query in queries:
            try:
                results = await self._search(source_id, query, max_results=max_items // len(queries))
                candidates.extend(results)
            except Exception as e:
                logger.error("arxiv_query_failed", query=query, error=str(e))

        # Deduplicate by URL within provider results
        seen = set()
        unique = []
        for c in candidates:
            if c.url not in seen:
                seen.add(c.url)
                unique.append(c)

        logger.info("arxiv_discovery_complete", source_id=str(source_id), count=len(unique))
        return unique

    async def _search(
        self,
        source_id: uuid.UUID,
        query: str,
        max_results: int = 10,
    ) -> List[ContentCandidate]:
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(ARXIV_API_BASE, params=params)
            resp.raise_for_status()

        root = ET.fromstring(resp.text)
        candidates = []

        for entry in root.findall(f"{{{ARXIV_NS}}}entry"):
            try:
                candidate = self._entry_to_candidate(entry, source_id)
                if candidate:
                    candidates.append(candidate)
            except Exception as e:
                logger.warning("arxiv_entry_parse_error", error=str(e))

        return candidates

    def _entry_to_candidate(self, entry, source_id: uuid.UUID) -> Optional[ContentCandidate]:
        def text(tag: str) -> str:
            el = entry.find(f"{{{ARXIV_NS}}}{tag}")
            return el.text.strip() if el is not None and el.text else ""

        title = text("title").replace("\n", " ").strip()
        abstract = text("summary").replace("\n", " ").strip()
        url = ""

        for link in entry.findall(f"{{{ARXIV_NS}}}link"):
            if link.get("type") == "text/html":
                url = link.get("href", "")
                break

        if not url:
            id_el = entry.find(f"{{{ARXIV_NS}}}id")
            url = id_el.text.strip() if id_el is not None else ""

        if not url or not title:
            return None

        # Parse publication date
        published_at = None
        pub_el = entry.find(f"{{{ARXIV_NS}}}published")
        if pub_el is not None and pub_el.text:
            try:
                published_at = datetime.fromisoformat(pub_el.text.replace("Z", "+00:00"))
            except Exception:
                pass

        # Authors
        authors = []
        for author_el in entry.findall(f"{{{ARXIV_NS}}}author"):
            name_el = author_el.find(f"{{{ARXIV_NS}}}name")
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())

        return ContentCandidate(
            title=title,
            url=url,
            source_id=source_id,
            content_type="paper",
            author=", ".join(authors[:3]) if authors else None,
            published_at=published_at,
            abstract=abstract[:1000] if abstract else None,
            raw_metadata={"source": "arxiv"},
        )

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                r = await client.get(ARXIV_API_BASE, params={"search_query": "test", "max_results": 1})
                return r.status_code == 200
        except Exception:
            return False
