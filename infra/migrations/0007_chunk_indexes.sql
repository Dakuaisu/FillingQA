-- 0007: search indexes on chunks, exactly as PRD 8 writes them. PRD 14 Phase 2
-- step 4, built after the bulk load (0005 deliberately left them out).
--
-- chunks_hnsw: approximate nearest neighbour over normalized bge vectors, cosine.
-- chunks_tsv:  full-text search over the generated tsv column from 0005.

CREATE INDEX IF NOT EXISTS chunks_hnsw ON chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS chunks_tsv ON chunks USING gin (tsv);
