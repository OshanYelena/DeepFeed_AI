"""
DeepFeed AI - RSS Source Provider (M5)
Discovers content from RSS/Atom feeds using feedparser.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
import feedparser
from domain.interfaces.source_provider import SourceProvider, ContentCandidate
from logger import get_logger

logger = get_logger(__name__)


class RSSProvider(SourceProvider):
    """Discovers content from RSS and Atom feeds."""

    @property
    def provider_name(self) -> str:
        return "rss"

    async def discover(
        self,
        source_id: uuid.UUID,
        base_url: str,
        search_queries: Optional[List[str]] = None,
        max_items: int = 50,
    ) -> List[ContentCandidate]:
        logger.info("rss_discovery_start", source_id=str(source_id), url=base_url)
        candidates: List[ContentCandidate] = []

        try:
            feed = feedparser.parse(base_url)
            if feed.bozo and not feed.entries:
                logger.warning("rss_feed_parse_error", url=base_url, error=str(feed.bozo_exception))
                return []

            for entry in feed.entries[:max_items]:
                try:
                    candidate = self._entry_to_candidate(entry, source_id)
                    if candidate:
                        candidates.append(candidate)
                except Exception as e:
                    logger.warning("rss_entry_parse_error", url=base_url, error=str(e))
                    continue

            logger.info("rss_discovery_complete", source_id=str(source_id), count=len(candidates))
        except Exception as e:
            logger.error("rss_discovery_failed", source_id=str(source_id), error=str(e))

        return candidates

    def _entry_to_candidate(self, entry: dict, source_id: uuid.UUID) -> Optional[ContentCandidate]:
        url = entry.get("link", "")
        title = entry.get("title", "")

        if not url or not title:
            return None

        published_at = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                import time
                ts = time.mktime(entry.published_parsed)
                published_at = datetime.fromtimestamp(ts, tz=timezone.utc)
            except Exception:
                pass

        author = entry.get("author", None)
        abstract = entry.get("summary", None)
        if abstract:
            # Strip HTML from summary
            from bs4 import BeautifulSoup
            abstract = BeautifulSoup(abstract, "lxml").get_text(separator=" ", strip=True)[:500]

        return ContentCandidate(
            title=title,
            url=url,
            source_id=source_id,
            content_type="article",
            author=author,
            published_at=published_at,
            abstract=abstract,
        )

    async def health_check(self) -> bool:
        return True
