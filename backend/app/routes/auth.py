from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
from app.auth.auth_handler import create_access_token, verify_password
from app.schemas.auth import LoginRequest, Token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Endpoint for assessor login.
    """
    # Query the accessor_table
    query = text("SELECT * FROM accessor_table WHERE accessor_id = :id")
    result = db.execute(query, {"id": login_data.accessor_id}).fetchone()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Accessor ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check password (mapping columns based on our check: accessor_id, password, name)
    # result is a tuple: (id, password, name)
    if not verify_password(login_data.password, result.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token
    access_token = create_access_token(data={"sub": result.accessor_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "name": result.name
    }
