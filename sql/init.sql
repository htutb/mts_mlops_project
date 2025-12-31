CREATE TABLE IF NOT EXISTS predictions (
    request_id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    toxic_score DOUBLE PRECISION NOT NULL,
    is_toxic BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    batch_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_predictions_created_at
ON predictions (created_at);

CREATE INDEX IF NOT EXISTS idx_predictions_is_toxic
ON predictions (is_toxic);

CREATE INDEX IF NOT EXISTS idx_predictions_batch_id
ON predictions (batch_id);