# app/core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from bson import ObjectId
from app.models.application import Application
from app.services.auth_service import AuthService

security = HTTPBearer()

async def get_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[str]:
    if credentials:
        auth_service = AuthService()
        app = await auth_service.verify_api_key(credentials.credentials)
        if not app:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        return str(app.id)
    return None

async def get_api_key_required(
    api_key: Optional[str] = Depends(get_api_key)
) -> str:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    return api_key