from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    accessor_id: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    name: str

class TokenData(BaseModel):
    accessor_id: Optional[str] = None
