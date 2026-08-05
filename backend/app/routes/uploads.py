from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
from app.services.upload_service import UploadService
from app.routes.auth import get_current_accessor
from pydantic import BaseModel
from typing import Optional
import uuid
import json

router = APIRouter(prefix="/upload", tags=["Uploads & Claims"])

@router.post("/tc")
async def upload_tc(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and index global Terms & Conditions.
    """
    file_path = await UploadService.save_upload(file, "tc")
    num_chunks = await UploadService.process_tc(db, file_path)
    
    return {
        "message": "Global T&C uploaded and indexed successfully",
        "chunks_created": num_chunks
    }

@router.post("/submit")
async def submit_new_claim(
    customer_name: str = Form(...),
    claim_type: str = Form(...),
    policy_file: UploadFile = File(...),
    claim_file: UploadFile = File(None),
    claim_text: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Unified endpoint: Uploads policy and submits claim in one request.
    """
    if not claim_file and not claim_text:
        raise HTTPException(status_code=400, detail="Please provide a claim file or claim text.")

    try:
        print(f"--- Starting upload for {customer_name} ---")
        # 1. Process Policy
        print("Saving policy file...")
        policy_path = await UploadService.save_upload(policy_file, "policies")
        print(f"Policy saved at {policy_path}")
        
        # Insert Policy into DB
        print("Inserting policy into database...")
        p_query = text("INSERT INTO policy (location) VALUES (:loc) RETURNING policy_id")
        p_result = db.execute(p_query, {"loc": policy_path})
        policy_id = p_result.fetchone()[0]
        # Commit NOW so vector_service's separate SessionLocal can see the policy row
        # (FK constraint on policy_chunks.policy_id requires it to exist in policy table)
        db.commit()
        print(f"Policy inserted with ID: {policy_id}")
        
        # Index Policy for RAG (For future use by teammates)
        print("Processing and indexing policy for RAG...")
        await UploadService.process_policy(db, policy_path, str(policy_id))
        print("Policy indexing complete.")

        # 2. Process Claim
        print("Saving claim file...")
        claim_path = None
        if claim_file:
            claim_path = await UploadService.save_upload(claim_file, "claims")
            print(f"Claim saved at {claim_path}")
        
        # Insert Claim into DB
        print("Inserting claim into database...")
        c_query = text("""
            INSERT INTO claim (policy_id, customer_name, claim_type, result)
            VALUES (:p_id, :c_name, :c_type, :res)
            RETURNING claim_id
        """)
        c_result = db.execute(c_query, {
            "p_id": policy_id,
            "c_name": customer_name,
            "c_type": claim_type,
            "res": "Ready for Assessment"
        })
        claim_id = c_result.fetchone()[0]
        db.commit()
        print(f"Claim inserted with ID: {claim_id}. Transaction committed.")

        # Extract full claim text for assessment
        from app.services.file_service import FileService
        final_claim_text = claim_text
        if not final_claim_text and claim_path:
            final_claim_text = await FileService.get_document_text(claim_path)
            
        # Trigger assessment via Groq/FAISS Pipeline
        from app.rag.pipeline import rag_pipeline
        assessment = await rag_pipeline.process_assessment(db, claim_id, str(final_claim_text))

        try:
            import json
            parsed_assessment = json.loads(assessment)
        except Exception:
            parsed_assessment = assessment

        # Return successful upload details
        return {
            "message": "Policy and claim processed and assessed successfully",
            "claim_id": claim_id,
            "policy_id": policy_id,
            "status": "Assessed",
            "assessment": parsed_assessment
        }

    except Exception as e:
        db.rollback()
        print(f"Unified upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Error during unified upload: {str(e)}")

@router.get("/policy/{policy_id}/claims")
async def get_claims_by_policy(policy_id: int, db: Session = Depends(get_db)):
    """
    Retrieves all claims submitted for a specific policy.
    """
    query = text("SELECT * FROM claim WHERE policy_id = :pid ORDER BY claim_id DESC")
    results = db.execute(query, {"pid": policy_id}).fetchall()

    if not results:
        raise HTTPException(status_code=404, detail=f"No claims found for policy_id {policy_id}")

    claims = []
    for row in results:
        try:
            assessment = json.loads(row.result) if row.result else None
        except Exception:
            assessment = row.result

        claims.append({
            "claim_id":      row.claim_id,
            "customer_name": row.customer_name,
            "claim_type":    row.claim_type,
            "assessment":    assessment,
            "final_decision": getattr(row, 'final_decision', None),
            "reviewed_by":   getattr(row, 'reviewed_by', None),
            "reviewed_at":   getattr(row, 'reviewed_at', None)
        })

    return {
        "policy_id":   policy_id,
        "total_claims": len(claims),
        "claims":      claims
    }


@router.get("/claims")
async def get_all_claims(db: Session = Depends(get_db)):
    """
    Returns all claims with fully parsed AI assessment results, newest first.
    Used by the Dashboard to display and inspect claims from the DB.
    """
    query = text("SELECT * FROM claim ORDER BY claim_id DESC")
    results = db.execute(query).fetchall()

    claims = []
    for row in results:
        try:
            assessment = json.loads(row.result) if row.result else {}
        except Exception:
            assessment = {}

        claims.append({
            "claim_id":      row.claim_id,
            "policy_id":     row.policy_id,
            "customer_name": row.customer_name,
            "claim_type":    row.claim_type,
            "decision":      assessment.get("decision", "Pending"),
            "justification": assessment.get("justification", ""),
            "flags":         assessment.get("flags", []),
            "final_decision": getattr(row, 'final_decision', None),
            "reviewed_by":   getattr(row, 'reviewed_by', None),
            "reviewed_at":   getattr(row, 'reviewed_at', None)
        })

    return {"total": len(claims), "claims": claims}


@router.get("/{claim_id}")
async def get_claim_status(claim_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the full parsed assessment for a single claim by ID.
    """
    query = text("SELECT * FROM claim WHERE claim_id = :id")
    result = db.execute(query, {"id": claim_id}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Claim not found")

    try:
        assessment = json.loads(result.result) if result.result else {}
    except Exception:
        assessment = {}

    return {
        "claim_id":      result.claim_id,
        "policy_id":     result.policy_id,
        "customer_name": result.customer_name,
        "claim_type":    result.claim_type,
        "decision":      assessment.get("decision", "Pending"),
        "justification": assessment.get("justification", ""),
        "flags":         assessment.get("flags", []),
        "final_decision": getattr(result, 'final_decision', None),
        "reviewed_by":   getattr(result, 'reviewed_by', None),
        "reviewed_at":   getattr(result, 'reviewed_at', None)
    }

class ReviewPayload(BaseModel):
    final_decision: str
    reviewer_note: Optional[str] = None

@router.patch("/{claim_id}/review")
async def review_claim(
    claim_id: int, 
    payload: ReviewPayload, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_accessor)
):
    """
    Allows a human accessor to override the AI decision.
    """
    query = text("""
        UPDATE claim 
        SET final_decision = :fd, 
            reviewed_by = :accessor_id, 
            reviewed_at = NOW() 
        WHERE claim_id = :id
        RETURNING claim_id, final_decision, reviewed_by, reviewed_at
    """)
    result = db.execute(query, {
        "fd": payload.final_decision,
        "accessor_id": current_user.get("accessor_id"),
        "id": claim_id
    }).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    db.commit()
    return {
        "message": "Claim reviewed successfully",
        "claim_id": result.claim_id,
        "final_decision": result.final_decision,
        "reviewed_by": result.reviewed_by,
        "reviewed_at": result.reviewed_at
    }
