from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth 

bearer_scheme = HTTPBearer()


async def get_current_user(token: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    
    if token is None or token.scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer 토큰이 필요합니다.",
        )
    try:
       
        decoded_token = auth.verify_id_token(token.credentials)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"유효하지 않은 Firebase 토큰입니다: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
