"""
DeepFeed AI - Content Processing Service (M7)
Handles HTML/PDF extraction, cleaning, and topic classification.
Pipeline: Fetch → Extract → Clean → Classify → Store
"""
import uuid
import httpx
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.database.models import ContentItem, ProcessedContent, ContentTopic
from domain.interfaces.llm_provider import LLMProvider
from config import settings
from logger import get_logger

logger = get_logger(__name__)


class ContentExtractor:
    """Handles HTML and PDF content extraction (TDS §11.4, §11.5)."""

    async def extract_html(self, url: str) -> tuple[str, int]:
        """
        Fetch and extract clean text from an HTML URL.
        Returns (clean_text, word_count).
        """
        try:
            async with httpx.AsyncClient(
                timeout=settings.extraction_timeout_seconds,
                follow_redirects=True,
                headers={"User-Agent": "DeepFeedAI/1.0 (content aggregator)"},
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                html = resp.text

            # Use readability for main content extraction
            try:
                from readability import Document
                doc = Document(html)
                content_html = doc.summary()
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content_html, "lxml")
                clean_text = soup.get_text(separator="\n", strip=True)
            except Exception:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, "lxml")
                # Remove script and style tags
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                clean_text = soup.get_text(separator="\n", strip=True)

            word_count = len(clean_text.split())
            return clean_text[:50000], word_count  # Cap at 50k chars

        except Exception as e:
            logger.warning("html_extraction_failed", url=url, error=str(e))
            raise

    async def extract_pdf(self, url: str) -> tuple[str, int]:
        """
        Download and extract text from a PDF URL.
        Returns (clean_text, word_count).
        """
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                pdf_bytes = resp.content

            try:
                import fitz  # PyMuPDF
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                pages = []
                for page in doc:
                    pages.append(page.get_text())
                clean_text = "\n".join(pages)
            except Exception:
                import pdfplumber
                import io
                with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                    pages = [p.extract_text() or "" for p in pdf.pages]
                clean_text = "\n".join(pages)

            word_count = len(clean_text.split())
            return clean_text[:50000], word_count

        except Exception as e:
            logger.warning("pdf_extraction_failed", url=url, error=str(e))
            raise


class TopicClassifier:
    """
    Classifies content topics using LLM or keyword matching.
    Falls back to keyword extraction if LLM is unavailable.
    """

    _KNOWN_TOPICS = [
        "Machine Learning", "Deep Learning", "Reinforcement Learning",
        "Natural Language Processing", "Computer Vision", "AI Agents",
        "Multi-Agent Systems", "Large Language Models", "Robotics",
        "Software Architecture", "Distributed Systems", "Cloud Computing",
        "DevOps", "Security", "Databases", "Frontend", "Backend",
        "Research", "Mathematics", "Statistics",
    ]

    def __init__(self, llm_provider: Optional[LLMProvider] = None) -> None:
        self._llm = llm_provider

    async def classify(self, text: str, title: str) -> List[dict]:
        """
        Returns list of {name, confidence} topic dicts.
        """
        if self._llm:
            try:
                return await self._classify_with_llm(text[:3000], title)
            except Exception as e:
                logger.warning("llm_classification_failed", error=str(e))

        return self._classify_with_keywords(text + " " + title)

    async def _classify_with_llm(self, text: str, title: str) -> List[dict]:
        prompt = f"""Classify this content into relevant technical topics.
Title: {title}
Content excerpt: {text[:2000]}

Return ONLY a JSON array like: [{{"name": "Topic Name", "confidence": 0.95}}]
Use only the most relevant topics (max 5). Be precise."""

        response = await self._llm.generate(prompt, max_tokens=300)
        import json
        import re
        # Extract JSON array from response
        match = re.search(r'\[.*?\]', response.content, re.DOTALL)
        if match:
            topics = json.loads(match.group())
            return [{"name": t.get("name", ""), "confidence": float(t.get("confidence", 0.5))} for t in topics if t.get("name")]
        return []

    def _classify_with_keywords(self, text: str) -> List[dict]:
        text_lower = text.lower()
        results = []
        for topic in self._KNOWN_TOPICS:
            keywords = topic.lower().split()
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                confidence = min(0.5 + (matches * 0.15), 0.95)
                results.append({"name": topic, "confidence": confidence})

        # Sort by confidence, return top 5
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results[:5]


class ContentProcessingService:
    """
    Orchestrates the content processing pipeline (TDS §11.2):
    Fetch → Extract → Clean → Classify → Store
    """

    def __init__(self, db: AsyncSession, llm_provider: Optional[LLMProvider] = None) -> None:
        self._db = db
        self._extractor = ContentExtractor()
        self._classifier = TopicClassifier(llm_provider)

    async def process_content_item(self, content_item_id: uuid.UUID, trace_id: str) -> bool:
        """
        Process a single ContentItem through the full pipeline.
        Returns True if successful.
        """
        result = await self._db.execute(
            select(ContentItem).where(ContentItem.id == content_item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            logger.error("content_item_not_found", content_item_id=str(content_item_id), trace_id=trace_id)
            return False

        logger.info("content_processing_start", content_item_id=str(content_item_id), url=item.url, trace_id=trace_id)

        try:
            # Step 1: Extract
            if item.url.endswith(".pdf"):
                clean_text, word_count = await self._extractor.extract_pdf(item.url)
                quality = "high" if word_count > 100 else "low"
            else:
                clean_text, word_count = await self._extractor.extract_html(item.url)
                quality = "high" if word_count > 200 else "medium" if word_count > 50 else "low"

            # Step 2: Detect language (simple heuristic)
            language = "en"

            # Step 3: Save processed content
            processed = ProcessedContent(
                content_item_id=item.id,
                clean_text=clean_text,
                word_count=word_count,
                language=language,
                extraction_quality=quality,
            )
            self._db.add(processed)

            # Step 4: Classify topics
            topics_data = await self._classifier.classify(clean_text[:3000], item.title)
            for topic in topics_data:
                ct = ContentTopic(
                    content_item_id=item.id,
                    topic_name=topic["name"],
                    confidence=topic["confidence"],
                )
                self._db.add(ct)

            # Step 5: Update item status
            item.status = "processed"
            await self._db.flush()

            logger.info(
                "content_processed",
                content_item_id=str(content_item_id),
                word_count=word_count,
                quality=quality,
                topics=len(topics_data),
                trace_id=trace_id,
            )
            return True

        except Exception as e:
            item.status = "failed"
            logger.error("content_processing_failed", content_item_id=str(content_item_id), error=str(e), trace_id=trace_id)
            return False

    async def process_pending(self, batch_size: int = 20, trace_id: str = "") -> int:
        """Process a batch of discovered but unprocessed content items.

        Returns the number of items *attempted* (i.e. how many were still
        'discovered'), not how many succeeded. Callers that loop batches
        until the backlog is drained (run_pipeline.py's run_processing_all)
        rely on this to know when to stop — a batch that fetched 20 items
        and failed all 20 is not the same as a batch that fetched 0 items
        because there was nothing left. Returning success_count here used
        to conflate those two cases: an unlucky batch where every item
        failed extraction (e.g. a handful of unreachable sources) made the
        caller believe the queue was empty and stop early, leaving the
        rest of the backlog stuck at 'discovered' indefinitely.
        """
        result = await self._db.execute(
            select(ContentItem)
            .where(ContentItem.status == "discovered")
            .limit(batch_size)
        )
        items = list(result.scalars().all())

        success_count = 0
        for item in items:
            ok = await self.process_content_item(item.id, trace_id)
            if ok:
                success_count += 1

        logger.info(
            "process_pending_batch_done",
            attempted=len(items),
            succeeded=success_count,
            trace_id=trace_id,
        )
        return len(items)
