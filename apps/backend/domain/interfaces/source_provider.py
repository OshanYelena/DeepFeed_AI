"""
DeepFeed AI - Source Provider Interface
All source providers must implement this interface (TDS §10.3).
Provider Pattern enforced via ABC.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List
import uuid


@dataclass
class ContentCandidate:
    """Raw content discovered by a provider before deduplication."""
    title: str
    url: str
    source_id: uuid.UUID
    content_type: str = "article"
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    abstract: Optional[str] = None
    raw_metadata: dict = field(default_factory=dict)

    @property
    def canonical_url(self) -> str:
        """Normalize URL for deduplication."""
        return self.url.rstrip("/").lower().split("?")[0]


class SourceProvider(ABC):
    """
    Base interface for all content source providers.
    Every provider must implement discover().
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique provider identifier."""
        ...

    @abstractmethod
    async def discover(
        self,
        source_id: uuid.UUID,
        base_url: str,
        search_queries: Optional[List[str]] = None,
        max_items: int = 50,
    ) -> List[ContentCandidate]:
        """
        Discover content from the source.
        Returns a list of ContentCandidates for deduplication and storage.
        """
        ...

    async def health_check(self) -> bool:
        """Check if the provider is reachable. Default: True."""
        return True
