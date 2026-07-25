import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Connecting to: {DATABASE_URL[:50]}...")

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 10})
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ DB Connection OK")

        # Check tables exist
        tables = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)).fetchall()
        print(f"\n📋 Tables found ({len(tables)}):")
        for t in tables:
            print(f"   - {t[0]}")

        # Check accessor_table for login
        try:
            users = conn.execute(text("SELECT accessor_id, name FROM accessor_table")).fetchall()
            print(f"\n👤 Accessors in DB ({len(users)}):")
            for u in users:
                print(f"   - ID: {u[0]}, Name: {u[1]}")
        except Exception as e:
            print(f"\n⚠️  accessor_table error: {e}")

        # Check policy table
        try:
            policies = conn.execute(text("SELECT COUNT(*) FROM policy")).fetchone()
            print(f"\n📄 Policies in DB: {policies[0]}")
        except Exception as e:
            print(f"\n⚠️  policy table error: {e}")

        # Check claim table
        try:
            claims = conn.execute(text("SELECT COUNT(*) FROM claim")).fetchone()
            print(f"📝 Claims in DB: {claims[0]}")
        except Exception as e:
            print(f"\n⚠️  claim table error: {e}")

except Exception as e:
    print(f"❌ Connection FAILED: {e}")
