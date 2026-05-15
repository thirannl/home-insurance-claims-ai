import os
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.vector_service import vector_service
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

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
        prompt = f"""
        You are a professional Insurance Claim Assessor. 
        Analyze the following CLAIM based ONLY on the provided POLICY CLAUSES and TERMS & CONDITIONS.

        CLAIM:
        {claim_text}

        CONTEXT:
        {context}

        INSTRUCTIONS:
        1. Determine if the claim is "Covered", "Not Covered", or requires "Manual Review".
        2. Provide a clear, concise reasoning.
        3. Identify specific clauses that support your decision.
        4. Return your response in EXACT JSON format:
        {{
            "status": "Covered" | "Not Covered" | "Manual Review",
            "reasoning": "string",
            "supporting_clauses": ["string"],
            "confidence_score": 0.0 to 1.0
        }}
        """

        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content

    @classmethod
    async def process_assessment(cls, db: Session, claim_id: int) -> Dict[str, Any]:
        """
        Full orchestration of claim assessment.
        """
        query = text("SELECT * FROM claim WHERE claim_id = :id")
        claim = db.execute(query, {"id": claim_id}).fetchone()
        
        if not claim:
            raise ValueError(f"Claim ID {claim_id} not found")

        search_query = f"Claim for {claim.claim_type}. Details: {claim.customer_name}"
        context = cls.get_context(search_query, claim.policy_id)
        
        assessment_json = cls.assess_claim(search_query, context)
        
        update_query = text("UPDATE claim SET result = :res WHERE claim_id = :id")
        db.execute(update_query, {"res": assessment_json, "id": claim_id})
        db.commit()
        
        return assessment_json

rag_pipeline = RAGPipeline()
