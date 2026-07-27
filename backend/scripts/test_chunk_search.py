import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from sqlalchemy import text
from app.db.database import SessionLocal
from app.services.vector_service import vector_service

db = SessionLocal()
pid = db.execute(text("INSERT INTO policy (location) VALUES ('test-location') RETURNING policy_id")).fetchone()[0]
print(f"Inserted dummy policy, policy_id={pid}")
zero_vec = "[" + ",".join(["0.0"] * 384) + "]"
db.execute(text(f"INSERT INTO policy_chunks (policy_id, content, embedding) VALUES (:pid, :content, '{zero_vec}'::vector)"),
           {"pid": pid, "content": "Dummy clause: fire damage is covered up to policy limit."})
db.commit(); db.close()
print("Inserted dummy chunk into policy_chunks")
result = vector_service.search_index("test query", str(pid), top_k=1)
print("search_index result:", result)
