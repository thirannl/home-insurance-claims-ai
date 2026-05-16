import os
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.vector_service import vector_service
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
        prompt = f"""
        You are an expert insurance claims assessor.
        Your task is to evaluate a claim using ONLY the provided policy and terms.

        ----------------------------
        STRICT RULES (MANDATORY)
        ----------------------------
        1. Use ONLY the given claim, policy, and terms.
        2. Do NOT invent or assume anything.
        3. Do NOT reinterpret or modify the claim.
        4. Do NOT use unrelated policy sections.
        5. Check numerical calculation correctly.
        6. check date in correctly if needed for date of incident and date of reporting

        ----------------------------
        CRITICAL DECISION RULES
        ----------------------------
        1. Exclusions override everything.
        2. Limits override coverage.
        3. You MUST check limits BEFORE giving final decision.
        4. If claim amount exceeds policy limit AND endorsement is NOT provided:
           -> "Check limits carefully" and perform numerical calculation correctly 
           -> FINAL DECISION MUST BE "Needs Human Review"
        5. You are NOT allowed to return "Covered" if limits are violated.
        6. If a required condition for coverage is explicitly NOT satisfied in the claim -> decision MUST be "Not Covered".
        7. Do NOT return "Needs Human Review" when the claim clearly violates a condition.

        ----------------------------
        MANDATORY DECISION FLOW
        ----------------------------
        Follow ALL steps in order:

        Step 1: Identify incident type  
        Step 2: Check if covered (if not follow any one point -> RETURN "Not Covered", STOP here)
        Step 3: Check exclusions  
        Step 4: Check limits (CRITICAL)
            - If claim amount > limit:
                -> Check endorsement
                -> If endorsement NOT mentioned:
                    -> RETURN "Needs Human Review" (STOP here)
        Step 5: Check conditions
        - If condition is clearly satisfied -> continue
        - If condition is missing -> Needs Human Review
        - If condition is clearly NOT satisfied -> Not Covered (STOP)
        Step 6: Check terms and conditions (important)
               - check terms and condition on each point whether it suit for this claim and considered this.
               - if(not follow any point -> RETURN "Needs Human Review" (STOP here))
        Step 7: Final decision  

        ----------------------------
        INPUT
        ----------------------------
        CLAIM DETAILS:
        {claim_text}

        RETRIEVED CONTEXT (POLICY & T&C):
        {context}

        ----------------------------
        OUTPUT (STRICT JSON ONLY)
        ----------------------------
        Return ONLY valid JSON. 
        Rules for flags:
        - flags MUST NOT be empty
        - Any conditions that must be met for the claim to proceed
        - If claim exceeds limit -> include flag: "Claim exceeds policy limit"
        - If endorsement missing -> include flag: "Endorsement not available"
        - If information missing -> include flag describing missing data

        {{
          "decision": "Covered" | "Not Covered" | "Needs Human Review",
          "justification": "Short explanation based on policy",
          "flags": ["at least one meaningful flag if applicable"]
        }}
        """


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
