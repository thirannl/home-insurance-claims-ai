-- =========================
-- T&C TABLE
-- =========================

CREATE TABLE terms_and_conditions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    location TEXT NOT NULL
);


-- =========================
-- POLICY TABLE
-- =========================

CREATE TABLE policy (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    location TEXT NOT NULL
);


-- =========================
-- CLAIM TABLE
-- =========================

CREATE TABLE claim (
    claim_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_id BIGINT REFERENCES policy(policy_id)
    ON DELETE CASCADE,

    customer_name TEXT NOT NULL,

    claim_type TEXT NOT NULL,

    claim_time TIMESTAMPTZ DEFAULT NOW(),

    result TEXT
);

-- =========================
-- Assesor TABLE
-- =========================

CREATE TABLE accessor_table (

    accessor_id TEXT PRIMARY KEY,

    password TEXT NOT NULL,

    name TEXT NOT NULL

);