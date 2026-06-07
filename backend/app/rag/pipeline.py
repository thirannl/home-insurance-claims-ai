import os
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.vector_service import vector_service
from app.prompts.assessment import ASSESSMENT_PROMPT
from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class RAGPipeline:
    @staticmethod
    def get_context(query: str, policy_id: int, top_k: int = 3) -> str:
        """
        Retrieves relevant context from Policy and Global T&C using LangChain search.
        """
        # 1. Search Policy Index (Now using strings directly thanks to LangChain)
        policy_context = vector_service.search_index(query, str(policy_id), top_k=top_k)
        
        # 2. Search Global T&C Index
        tc_context = vector_service.search_index(query, "global_tc", top_k=top_k)
        
        context = "POLICY CLAUSES:\n" + "\n".join(policy_context)
        context += "\n\nSTANDARD TERMS & CONDITIONS:\n" + "\n".join(tc_context)
        
        return context

    @staticmethod
    def assess_claim(claim_text: str, context: str) -> str:
        """
        Calls Groq LLM to assess the claim based on context.
        """
        prompt = ASSESSMENT_PROMPT.format(
            claim_text=claim_text,
            context=context
        )


        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq API Error: {e}")
            import json
            return json.dumps({
                "decision": "Needs Human Review",
                "justification": f"Error connecting to Groq LLM: {str(e)}",
                "flags": ["System Error"]
            })

    @classmethod
    async def process_assessment(cls, db: Session, claim_id: int, claim_text: str) -> str:
        """
        Full orchestration of claim assessment.
        """
        query = text("SELECT * FROM claim WHERE claim_id = :id")
        claim = db.execute(query, {"id": claim_id}).fetchone()
        
        if not claim:
            raise ValueError(f"Claim ID {claim_id} not found")

        # Get relevant passages using the full claim text as the query
        context = cls.get_context(claim_text, claim.policy_id)
        
        # Assess claim using Groq LLM
        assessment_json = cls.assess_claim(claim_text, context)
        
        # Final output
        update_query = text("UPDATE claim SET result = :res WHERE claim_id = :id")
        db.execute(update_query, {"res": assessment_json, "id": claim_id})
        db.commit()
        
        return assessment_json

rag_pipeline = RAGPipeline()
