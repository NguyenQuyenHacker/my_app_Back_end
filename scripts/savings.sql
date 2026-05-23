-- Tạo bảng cho service Sổ tiết kiệm

-- Mở rộng CHECK constraint của transactions để chấp nhận transfer_type mới
ALTER TABLE transactions DROP CONSTRAINT IF EXISTS chk_transfer_type;
ALTER TABLE transactions
  ADD CONSTRAINT chk_transfer_type
  CHECK (transfer_type IN (
    'INTERNAL',
    'EXTERNAL',
    'SAVINGS_DEPOSIT',
    'SAVINGS_MATURITY',
    'SAVINGS_EARLY_WITHDRAWAL'
  ));

CREATE TABLE IF NOT EXISTS savings_products (
    product_id              UUID PRIMARY KEY,
    code                    VARCHAR(32) NOT NULL UNIQUE,
    name                    TEXT NOT NULL,
    term_months             INT NOT NULL,
    interest_rate           NUMERIC(6,4) NOT NULL,
    early_withdrawal_rate   NUMERIC(6,4) NOT NULL DEFAULT 0.0010,
    min_amount              NUMERIC(18,2) NOT NULL DEFAULT 100000.00,
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL,
    updated_at              TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_savings_products_is_active ON savings_products (is_active);

CREATE TABLE IF NOT EXISTS savings_accounts (
    savings_id              UUID PRIMARY KEY,
    savings_code            VARCHAR(32) NOT NULL UNIQUE,
    customer_id             UUID NOT NULL REFERENCES customers(customer_id),
    account_id              UUID NOT NULL REFERENCES accounts(account_id),
    product_id              UUID NOT NULL REFERENCES savings_products(product_id),
    principal_amount        NUMERIC(18,2) NOT NULL,
    interest_rate           NUMERIC(6,4) NOT NULL,
    early_withdrawal_rate   NUMERIC(6,4) NOT NULL,
    term_months             INT NOT NULL,
    start_date              TIMESTAMPTZ NOT NULL,
    maturity_date           TIMESTAMPTZ NOT NULL,
    status                  VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    interest_earned         NUMERIC(18,2) NOT NULL DEFAULT 0.00,
    final_amount            NUMERIC(18,2) NOT NULL DEFAULT 0.00,
    closed_at               TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL,
    updated_at              TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_savings_accounts_customer ON savings_accounts (customer_id);
CREATE INDEX IF NOT EXISTS ix_savings_accounts_status ON savings_accounts (status);
CREATE INDEX IF NOT EXISTS ix_savings_accounts_maturity ON savings_accounts (maturity_date);

-- Seed system accounts cần cho luồng tiết kiệm (chạy nếu chưa có)
INSERT INTO system_accounts (id, account_code, name, balance, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'SAVINGS_POOL', 'Pool tiền gửi tiết kiệm', 0, NOW(), NOW()),
    (gen_random_uuid(), 'INTEREST_EXPENSE', 'Chi phí lãi tiết kiệm', 0, NOW(), NOW())
ON CONFLICT (account_code) DO NOTHING;

-- Seed một số sản phẩm tiết kiệm mặc định
INSERT INTO savings_products (product_id, code, name, term_months, interest_rate, early_withdrawal_rate, min_amount, is_active, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'TK01M', 'Tiết kiệm 1 tháng',  1,  0.0350, 0.0010, 100000.00, TRUE, NOW(), NOW()),
    (gen_random_uuid(), 'TK03M', 'Tiết kiệm 3 tháng',  3,  0.0420, 0.0010, 100000.00, TRUE, NOW(), NOW()),
    (gen_random_uuid(), 'TK06M', 'Tiết kiệm 6 tháng',  6,  0.0510, 0.0010, 100000.00, TRUE, NOW(), NOW()),
    (gen_random_uuid(), 'TK12M', 'Tiết kiệm 12 tháng', 12, 0.0580, 0.0010, 100000.00, TRUE, NOW(), NOW()),
    (gen_random_uuid(), 'TK24M', 'Tiết kiệm 24 tháng', 24, 0.0620, 0.0010, 100000.00, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
