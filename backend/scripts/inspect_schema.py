import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from sqlalchemy import text
from app.db.database import SessionLocal

db = SessionLocal()
for tbl in ["policy", "policy_chunks"]:
    cols = db.execute(text(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=:t ORDER BY ordinal_position"
    ), {"t": tbl}).fetchall()
    print(f"--- {tbl} ---")
    for c in cols:
        print(f"  {c[0]}  ({c[1]})")
db.close()
