-- transfer_sessions: lưu tạm session init->confirm, TTL 5 phút
CREATE TABLE IF NOT EXISTS transfer_sessions (
    session_id        UUID PRIMARY KEY,
    customer_id       UUID NOT NULL,
    source_account_id UUID NOT NULL,
    transfer_type     VARCHAR(16) NOT NULL,
    payload           JSONB NOT NULL,
    used              BOOLEAN NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMPTZ NOT NULL,
    expires_at        TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_transfer_sessions_customer_id ON transfer_sessions (customer_id);
CREATE INDEX IF NOT EXISTS ix_transfer_sessions_expires_at ON transfer_sessions (expires_at);
