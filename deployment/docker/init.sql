-- DeepFeed AI - Database Initialization
-- pgvector is pre-installed in the pgvector/pgvector:pg16 image
-- These extensions are created in the 'deepfeed' database on first start

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;