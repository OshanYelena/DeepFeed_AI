"""
DeepFeed AI - Discovery Application Service (M4, M5, M6)
Manages sources and orchestrates content discovery with deduplication.
"""
import uuid
import hashlib
from typing import List, Optional, Dict, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.database.models import Source, ContentItem, SearchPlan
from infrastructure.providers.rss_provider import RSSProvider
from infrastructure.providers.arxiv_provider import ArXivProvider
from domain.interfaces.source_provider import SourceProvider, ContentCandidate
from domain.events.events import ContentDiscovered
from logger import get_logger

logger = get_logger(__name__)


class SourceService:
    """Manages source CRUD. Admin-only operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_source(self, name: str, source_type: str, base_url: str, trust_score: float, trace_id: str) -> Source:
        source = Source(name=name, source_type=source_type, base_url=base_url, trust_score=trust_score)
        self._db.add(source)
        await self._db.flush()
        logger.info("source_created", source_id=str(source.id), name=name, trace_id=trace_id)
        return source

    async def list_sources(self, active_only: bool = True) -> List[Source]:
        stmt = select(Source)
        if active_only:
            stmt = stmt.where(Source.is_active.is_(True))
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_source(self, source_id: uuid.UUID) -> Optional[Source]:
        result = await self._db.execute(select(Source).where(Source.id == source_id))
        return result.scalar_one_or_none()

    async def update_source(self, source_id: uuid.UUID, **kwargs) -> Source:
        source = await self.get_source(source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")
        for k, v in kwargs.items():
            setattr(source, k, v)
        return source

    async def disable_source(self, source_id: uuid.UUID, trace_id: str) -> None:
        source = await self.get_source(source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")
        source.is_active = False
        logger.info("source_disabled", source_id=str(source_id), trace_id=trace_id)


class DiscoveryService:
    """
    Orchestrates content discovery across all active sources.
    Handles provider dispatch, deduplication, and ContentItem creation.
    """

    _PROVIDER_REGISTRY: Dict[str, Type[SourceProvider]] = {
        "rss": RSSProvider,
        "arxiv": ArXivProvider,
    }

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _get_provider(self, source_type: str) -> Optional[SourceProvider]:
        cls = self._PROVIDER_REGISTRY.get(source_type)
        return cls() if cls else None

    async def run_discovery(
        self,
        source_id: Optional[uuid.UUID] = None,
        search_queries: Optional[List[str]] = None,
        trace_id: str = "",
    ) -> int:
        """
        Run discovery for all active sources (or a specific one).
        Returns number of new ContentItems created.
        """
        stmt = select(Source).where(Source.is_active.is_(True))
        if source_id:
            stmt = stmt.where(Source.id == source_id)

        result = await self._db.execute(stmt)
        sources = list(result.scalars().all())

        total_new = 0
        for source in sources:
            try:
                new_count = await self._discover_from_source(source, search_queries, trace_id)
                total_new += new_count
            except Exception as e:
                logger.error("source_discovery_error", source_id=str(source.id), error=str(e), trace_id=trace_id)

        logger.info("discovery_complete", total_new=total_new, trace_id=trace_id)
        return total_new

    async def _discover_from_source(
        self,
        source: Source,
        search_queries: Optional[List[str]],
        trace_id: str,
    ) -> int:
        provider = self._get_provider(source.source_type)
        if not provider:
            logger.warning("no_provider_for_source_type", source_type=source.source_type, trace_id=trace_id)
            return 0

        candidates = await provider.discover(
            source_id=source.id,
            base_url=source.base_url,
            search_queries=search_queries,
        )

        new_count = 0
        for candidate in candidates:
            created = await self._create_if_new(candidate, trace_id)
            if created:
                new_count += 1

        logger.info(
            "source_discovery_done",
            source_id=str(source.id),
            candidates=len(candidates),
            new=new_count,
            trace_id=trace_id,
        )
        return new_count

    async def _create_if_new(self, candidate: ContentCandidate, trace_id: str) -> bool:
        """Create ContentItem if not duplicate. Returns True if new item created."""
        canonical = candidate.canonical_url

        # Check canonical URL deduplication
        existing = await self._db.execute(
            select(ContentItem).where(ContentItem.canonical_url == canonical)
        )
        if existing.scalar_one_or_none():
            return False

        item = ContentItem(
            source_id=candidate.source_id,
            title=candidate.title,
            url=candidate.url,
            canonical_url=canonical,
            author=candidate.author,
            published_at=candidate.published_at,
            content_type=candidate.content_type,
            status="discovered",
        )
        self._db.add(item)
        await self._db.flush()

        logger.info("content_discovered", content_item_id=str(item.id), url=candidate.url, trace_id=trace_id)
        return True
