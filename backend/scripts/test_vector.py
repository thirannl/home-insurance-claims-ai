import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_service import vector_service

print("--- INSERT ---")
vector_service.create_and_save_index(
    ["This is a dummy test clause about fire damage coverage."], "1"
)
print("Chunk inserted for policy_id=1")

print("--- SEARCH ---")
result = vector_service.search_index("test query", "1", top_k=1)
print("Result:", result)
