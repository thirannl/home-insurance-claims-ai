from dotenv import load_dotenv
import os, pathlib
os.chdir(pathlib.Path(__file__).parent)
load_dotenv(override=True)
from sqlalchemy import create_engine, text

engine = create_engine(os.getenv("DATABASE_URL"))
with engine.connect() as conn:
    rows = conn.execute(
        text("SELECT accessor_id, password, name FROM accessor_table ORDER BY accessor_id")
    ).fetchall()

print(f"Rows returned: {len(rows)}")
print()
print(f"{'accessor_id':<15} {'password':<35} name")
print("-" * 75)
for r in rows:
    print(f"{str(r.accessor_id):<15} {str(r.password):<35} {str(r.name)}")
