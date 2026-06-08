"""
DeepFeed AI - Database Seed Script
Populates initial sources and admin user for development.
Run: python seed.py
"""
import asyncio
import uuid
from datetime import datetime, timezone

from infrastructure.database.connection import AsyncSessionLocal, engine
from infrastructure.database.models import Base, Source, User, UserProfile
from infrastructure.auth.passwords import hash_password
from logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

DEFAULT_SOURCES = [
    # arXiv feeds
    {"name": "arXiv - AI", "source_type": "arxiv", "base_url": "https://arxiv.org", "trust_score": 0.95},
    # High-quality RSS sources
    {"name": "OpenAI Blog", "source_type": "rss", "base_url": "https://openai.com/blog/rss.xml", "trust_score": 0.90},
    {"name": "Anthropic Research", "source_type": "rss", "base_url": "https://www.anthropic.com/news/rss.xml", "trust_score": 0.90},
    {"name": "Google DeepMind Blog", "source_type": "rss", "base_url": "https://deepmind.google/blog/rss.xml", "trust_score": 0.92},
    {"name": "Hugging Face Blog", "source_type": "rss", "base_url": "https://huggingface.co/blog/feed.xml", "trust_score": 0.88},
    {"name": "PyTorch Blog", "source_type": "rss", "base_url": "https://pytorch.org/feed.xml", "trust_score": 0.88},
    {"name": "LangChain Blog", "source_type": "rss", "base_url": "https://blog.langchain.dev/rss/", "trust_score": 0.82},
    {"name": "AWS Machine Learning Blog", "source_type": "rss", "base_url": "https://aws.amazon.com/blogs/machine-learning/feed/", "trust_score": 0.85},
    {"name": "Microsoft Research Blog", "source_type": "rss", "base_url": "https://www.microsoft.com/en-us/research/blog/feed/", "trust_score": 0.88},
    {"name": "Towards Data Science", "source_type": "rss", "base_url": "https://towardsdatascience.com/feed", "trust_score": 0.72},
    {"name": "The Gradient", "source_type": "rss", "base_url": "https://thegradient.pub/rss/", "trust_score": 0.85},
    {"name": "Ahead of AI", "source_type": "rss", "base_url": "https://magazine.sebastianraschka.com/feed", "trust_score": 0.87},
]

ADMIN_USER = {
    "email": "admin@deepfeed.ai",
    "password": "AdminDeepFeed123!",
    "full_name": "DeepFeed Admin",
    "role": "admin",
}


async def seed_database():
    logger.info("seed_start")

    async with AsyncSessionLocal() as db:
        # Seed sources
        seeded_sources = 0
        for src_data in DEFAULT_SOURCES:
            from sqlalchemy import select
            existing = await db.execute(
                select(Source).where(Source.base_url == src_data["base_url"])
            )
            if not existing.scalar_one_or_none():
                source = Source(**src_data)
                db.add(source)
                seeded_sources += 1

        # Seed admin user
        from sqlalchemy import select
        existing_admin = await db.execute(
            select(User).where(User.email == ADMIN_USER["email"])
        )
        if not existing_admin.scalar_one_or_none():
            admin = User(
                email=ADMIN_USER["email"],
                password_hash=hash_password(ADMIN_USER["password"]),
                full_name=ADMIN_USER["full_name"],
                role=ADMIN_USER["role"],
            )
            db.add(admin)
            await db.flush()
            profile = UserProfile(user_id=admin.id)
            db.add(profile)
            logger.info("admin_user_created", email=ADMIN_USER["email"])

        await db.commit()
        logger.info("seed_complete", sources_added=seeded_sources)
        print(f"✅ Seeded {seeded_sources} sources")
        print(f"✅ Admin user: {ADMIN_USER['email']} / {ADMIN_USER['password']}")


if __name__ == "__main__":
    asyncio.run(seed_database())
