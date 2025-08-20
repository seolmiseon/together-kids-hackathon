from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
import httpx 
import os

from database import get_db
from models import User as UserModel
from schemas import User, UserCreate, Token 

router = APIRouter(prefix="/auth", tags=["authentication"])

# --- 보안 및 JWT 유틸리티 함수 ---
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user_by_email(db: Session, email: str):
    return db.query(UserModel).filter(UserModel.email == email).first()

# --- 자체 회원가입 / 로그인 API ---
@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
    
    hashed_password = get_password_hash(user_data.password)
    db_user = UserModel(email=user_data.email, name=user_data.name, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    access_token = create_access_token(data={"sub": db_user.email})
    refresh_token = create_refresh_token(data={"sub": db_user.email})
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_email(db, form_data.username) # form_data.username is email
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 잘못되었습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

# --- 소셜 로그인 콜백 처리 API ---
@router.post("/{provider}/callback")
async def handle_social_callback(provider: str, body: dict = Body(...), db: Session = Depends(get_db)):
    access_token = body.get("access_token")
    id_token = body.get("id_token")

    user_info_url, headers = "", {}
    if provider == "google":
        if not id_token: raise HTTPException(status_code=400, detail="Google ID token is required")
        user_info_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
    elif provider in ["kakao", "naver"]:
        if not access_token: raise HTTPException(status_code=400, detail=f"{provider.capitalize()} access token is required")
        user_info_url = {"kakao": "https://kapi.kakao.com/v2/user/me", "naver": "https://openapi.naver.com/v1/nid/me"}[provider]
        headers = {'Authorization': f'Bearer {access_token}'}
    else:
        raise HTTPException(status_code=404, detail="Unsupported provider")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(user_info_url, headers=headers)
            response.raise_for_status()
            social_user_info = response.json()

        email, name = None, None
        if provider == 'google':
            email, name = social_user_info.get("email"), social_user_info.get("name")
        elif provider == 'kakao':
            email, name = social_user_info.get("kakao_account", {}).get("email"), social_user_info.get("properties", {}).get("nickname")
        elif provider == 'naver':
            email, name = social_user_info.get("response", {}).get("email"), social_user_info.get("response", {}).get("name")
        
        if not email: raise HTTPException(status_code=400, detail="Email not found in social provider token")

        user = get_user_by_email(db, email)
        if not user:
            user = UserModel(email=email, name=name)
            db.add(user)
            db.commit()
            db.refresh(user)

        app_access_token = create_access_token(data={"sub": user.email})
        app_refresh_token = create_refresh_token(data={"sub": user.email})

        return {
            "access_token": app_access_token,
            "refresh_token": app_refresh_token,
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {"id": user.id, "name": user.name, "email": user.email}
        }
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=400, detail=f"Invalid social token: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 토큰 갱신 API ---
@router.post("/refresh")
async def refresh_token_endpoint(body: dict = Body(...), db: Session = Depends(get_db)):
    refresh_token = body.get("refreshToken")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token is missing")
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None: raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user = get_user_by_email(db, email)
        if user is None: raise HTTPException(status_code=401, detail="User not found")

        new_access_token = create_access_token(data={"sub": user.email})
        
        return {
            "access_token": new_access_token,
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
