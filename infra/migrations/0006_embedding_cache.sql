-- 0006: content-hash embedding cache. PRD 14 Phase 2: "content-hash cached".
--
-- Keyed on what determines a vector: the exact text embedded (chunks.content_hash
-- is sha256 of chunks.text, header included) and the model at a pinned revision.
-- It outlives chunks on purpose: store.py deletes and reinserts a filing's chunks
-- on every re-chunk, and an unchanged chunk must not be re-embedded. A vector
-- from another model or revision can never be read back as current, because
-- model and revision are part of the key.

CREATE TABLE IF NOT EXISTS embedding_cache (
    content_hash CHAR(64)    NOT NULL,
    model        TEXT        NOT NULL,
    revision     TEXT        NOT NULL,
    embedding    VECTOR(768) NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (content_hash, model, revision)
);
