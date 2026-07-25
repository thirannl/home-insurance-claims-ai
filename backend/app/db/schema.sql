-- Enable the pgvector extension to work with embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Assessors Table
CREATE TABLE IF NOT EXISTS assessors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT CHECK (role IN ('admin', 'assessor')) DEFAULT 'assessor',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Customers Table
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Policies Table
CREATE TABLE IF NOT EXISTS policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    policy_number TEXT UNIQUE NOT NULL,
    document_url TEXT,
    version TEXT DEFAULT '1.0',
    uploaded_by UUID REFERENCES assessors(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Policy Chunks (Vector Store)
CREATE TABLE IF NOT EXISTS policy_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(384), -- Assuming 384 dimensions for sentence-transformers
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Terms & Conditions Chunks (Global Vector Store)
CREATE TABLE IF NOT EXISTS tc_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding VECTOR(384),
    metadata JSONB DEFAULT '{}',
    version TEXT DEFAULT '1.0',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Claims Table
CREATE TABLE IF NOT EXISTS claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessor_id UUID REFERENCES assessors(id),
    customer_id UUID REFERENCES customers(id),
    policy_id UUID REFERENCES policies(id),
    claim_notice_text TEXT,
    status TEXT CHECK (status IN ('pending', 'processing', 'completed', 'failed')) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Claim Outputs Table
CREATE TABLE IF NOT EXISTS claim_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID REFERENCES claims(id) ON DELETE CASCADE,
    decision TEXT CHECK (decision IN ('Covered', 'Not Covered', 'Needs Human Review')),
    justification TEXT,
    matched_policy_clauses JSONB DEFAULT '[]',
    matched_tc_clauses JSONB DEFAULT '[]',
    flags JSONB DEFAULT '[]',
    confidence_score FLOAT,
    review_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_policy_chunks_embedding ON policy_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_tc_chunks_embedding ON tc_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_claims_customer ON claims(customer_id);
CREATE INDEX IF NOT EXISTS idx_policies_number ON policies(policy_number);
