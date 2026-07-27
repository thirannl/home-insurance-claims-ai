import os
from typing import List
from sqlalchemy import text
from app.embeddings.embedding_service import embedding_service
from app.db.database import SessionLocal
from dotenv import load_dotenv

load_dotenv()


def _vec_to_pg(vec: List[float]) -> str:
    """Formats a float list into PostgreSQL vector literal: '[0.1,0.2,...]'"""
    return "[" + ",".join(str(v) for v in vec) + "]"


class VectorService:
    def create_and_save_index(self, chunks: List[str], policy_id: str):
        """
        Embeds text chunks and persists them to pgvector tables.
        - policy_id == 'global_tc'  → tc_chunks table (no policy FK)
        - anything else             → policy_chunks table (policy_id as bigint)
        Keeps the same signature as the previous FAISS implementation so
        upload_service.py and rag/pipeline.py require no changes.
        """
        if not chunks:
            return None

        embed_model = embedding_service.get_embeddings_model()
        vectors = embed_model.embed_documents(chunks)  # List[List[float]]

        db = SessionLocal()
        try:
            if policy_id == "global_tc":
                # Delete stale rows first so re-uploads don't accumulate
                db.execute(text("DELETE FROM tc_chunks"))
                for chunk, vec in zip(chunks, vectors):
                    db.execute(
                        text(
                            "INSERT INTO tc_chunks (content, embedding) "
                            "VALUES (:content, CAST(:embedding AS vector))"
                        ),
                        {"content": chunk, "embedding": _vec_to_pg(vec)},
                    )
            else:
                # Remove existing chunks for this policy before re-indexing
                db.execute(
                    text("DELETE FROM policy_chunks WHERE policy_id = :pid"),
                    {"pid": policy_id},
                )
                for chunk, vec in zip(chunks, vectors):
                    db.execute(
                        text(
                            "INSERT INTO policy_chunks (policy_id, content, embedding) "
                            "VALUES (:pid, :content, CAST(:embedding AS vector))"
                        ),
                        {
                            "pid": policy_id,
                            "content": chunk,
                            "embedding": _vec_to_pg(vec),
                        },
                    )
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[VectorService] DB error during index creation: {e}")
            raise
        finally:
            db.close()

        return policy_id  # return something truthy (analogous to old folder_path)

    def search_index(self, query: str, policy_id: str, top_k: int = 3) -> List[str]:
        """
        Embeds the query and retrieves the top-k most similar chunks via
        pgvector cosine distance (<=>).
        Returns a list[str] with the same shape as the previous FAISS implementation.
        """
        embed_model = embedding_service.get_embeddings_model()
        query_vec = embed_model.embed_query(query)
        query_pg = _vec_to_pg(query_vec)

        db = SessionLocal()
        try:
            if policy_id == "global_tc":
                rows = db.execute(
                    text(
                        f"SELECT content FROM tc_chunks "
                        f"ORDER BY embedding <=> '{query_pg}'::vector "
                        f"LIMIT :k"
                    ),
                    {"k": top_k},
                ).fetchall()
            else:
                rows = db.execute(
                    text(
                        f"SELECT content FROM policy_chunks "
                        f"WHERE policy_id = :pid "
                        f"ORDER BY embedding <=> '{query_pg}'::vector "
                        f"LIMIT :k"
                    ),
                    {"pid": policy_id, "k": top_k},
                ).fetchall()

            return [row[0] for row in rows]

        except Exception as e:
            print(f"[VectorService] DB error during search: {e}")
            return []
        finally:
            db.close()


# Singleton instance — same name as before
vector_service = VectorService()
