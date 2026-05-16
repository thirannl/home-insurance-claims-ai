from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
from app.services.upload_service import UploadService
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
        # 1. Process Policy
        policy_path = await UploadService.save_upload(policy_file, "policies")
        
        # Insert Policy into DB
        p_query = text("INSERT INTO policy (location) VALUES (:loc) RETURNING policy_id")
        p_result = db.execute(p_query, {"loc": policy_path})
        policy_id = p_result.fetchone()[0]
        
        # Index Policy for RAG (For future use by teammates)
        await UploadService.process_policy(db, policy_path, str(policy_id))

        # 2. Process Claim
        claim_path = None
        if claim_file:
            claim_path = await UploadService.save_upload(claim_file, "claims")
        
        # Insert Claim into DB
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

@router.get("/{claim_id}")
async def get_claim_status(claim_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the status of a claim.
    """
    query = text("SELECT * FROM claim WHERE claim_id = :id")
    result = db.execute(query, {"id": claim_id}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {
        "claim_id": result.claim_id,
        "status": result.result
    }
