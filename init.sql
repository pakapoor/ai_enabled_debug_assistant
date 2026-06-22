CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
  id TEXT PRIMARY KEY,
  project TEXT NOT NULL,
  source_type TEXT NOT NULL, -- bug_report | git_diff | code_file
  source_id TEXT NOT NULL,   -- BUG-001 | commit sha | file path
  parent_id TEXT,
  chunk_index INT NOT NULL,
  chunk_text TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  embedding vector(384),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chunks_project ON chunks(project);
CREATE INDEX IF NOT EXISTS idx_chunks_source_type ON chunks(source_type);
CREATE INDEX IF NOT EXISTS idx_chunks_metadata_gin ON chunks USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_chunks_text_fts ON chunks USING GIN(to_tsvector('english', chunk_text));

-- Create vector index after enough rows are loaded in real use.
-- CREATE INDEX idx_chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops);
