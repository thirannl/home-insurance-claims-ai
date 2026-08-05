"""
Migration script: Add human override columns to the `claim` table.
Run once: python backend/scripts/migrate_add_review_columns.py
"""
import os
import sys

# Allow imports from the backend root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found in .env")

engine = create_engine(DATABASE_URL)

migration_sql = """
ALTER TABLE claim 
ADD COLUMN IF NOT EXISTS final_decision TEXT,
ADD COLUMN IF NOT EXISTS reviewed_by TEXT,
ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;
"""

with engine.begin() as conn:
    conn.execute(text(migration_sql))
    print("✅ Migration complete: final_decision, reviewed_by, reviewed_at added to `claim` table.")
