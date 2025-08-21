from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
import httpx 
import os

# from ..database import get_db
from ..database_sqlite import get_db
from ..database_sqlite import User as UserModel  # SQLite용 User 모델 사용
from ..schemas import User, UserCreate, Token 

router = APIRouter(prefix="/auth", tags=["authentication"])

# --- 보안 및 JWT 유틸리티 함수 ---
SECRET_KEY = os.getenv("SECRET_KEY", "together-kids-jwt-secret-2025-hackathon")
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
    print(f"=== 소셜 콜백 요청 수신: {provider} ===")
    print(f"Request body: {body}")
    
    access_token = body.get("access_token")
    id_token = body.get("id_token")
    
    print(f"Access token: {access_token}")
    print(f"ID token: {id_token}")

    user_info_url, headers = "", {}
    if provider == "google":
        if not id_token: raise HTTPException(status_code=400, detail="Google ID token is required")
        user_info_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
    elif provider in ["kakao", "naver"]:
        if not access_token: raise HTTPException(status_code=400, detail=f"{provider.capitalize()} access token is required")
        user_info_url = {"kakao": "https://kapi.kakao.com/v2/user/me", "naver": "https://openapi.naver.com/v1/nid/me"}[provider]
        headers = {'Authorization': f'Bearer {access_token}'}
        # 카카오의 경우 추가 스코프 요청
        if provider == "kakao":
            headers['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8'
    else:
        raise HTTPException(status_code=404, detail="Unsupported provider")

    try:
        print(f"=== 카카오 API 호출 시작 ===")
        print(f"URL: {user_info_url}")
        print(f"Headers: {headers}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(user_info_url, headers=headers)
            response.raise_for_status()
            social_user_info = response.json()

        print(f"=== 카카오 API 응답 ===")
        print(f"Response: {social_user_info}")

        email, name = None, None
        if provider == 'google':
            email, name = social_user_info.get("email"), social_user_info.get("name")
        elif provider == 'kakao':
            kakao_account = social_user_info.get("kakao_account", {})
            properties = social_user_info.get("properties", {})
            email = kakao_account.get("email")
            name = properties.get("nickname")
            
            # 이메일이 없는 경우 ID를 기반으로 임시 이메일 생성
            if not email:
                kakao_id = social_user_info.get("id")
                email = f"kakao_{kakao_id}@together-kids.temp"
                print(f"=== 임시 이메일 생성: {email} ===")
            
            # 닉네임이 없는 경우 임시 닉네임 생성
            if not name:
                name = f"카카오사용자_{kakao_id}"
                print(f"=== 임시 닉네임 생성: {name} ===")
                
        elif provider == 'naver':
            naver_response = social_user_info.get("response", {})
            email = naver_response.get("email")
            name = naver_response.get("name")
            
            # 네이버도 이메일이 없는 경우 임시 이메일 생성
            if not email:
                naver_id = naver_response.get("id")
                email = f"naver_{naver_id}@together-kids.temp"
                print(f"=== 네이버 임시 이메일 생성: {email} ===")
            
            # 이름이 없는 경우 임시 이름 생성
            if not name:
                name = f"네이버사용자_{naver_id}"
                print(f"=== 네이버 임시 닉네임 생성: {name} ===")
        
        print(f"=== 최종 사용자 정보 ===")
        print(f"Email: {email}, Name: {name}")
        
        if not email: 
            print(f"=== 심각한 에러: 여전히 이메일이 없음 ===")
            raise HTTPException(status_code=400, detail="Email not found in social provider token")

        user = get_user_by_email(db, email)
        if not user:
            print(f"=== 새 사용자 생성 ===")
            user = UserModel(email=email, name=name)
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            print(f"=== 기존 사용자 발견 ===")

        app_access_token = create_access_token(data={"sub": user.email})
        app_refresh_token = create_refresh_token(data={"sub": user.email})
        
        print(f"=== 토큰 생성 완료 ===")

        return {
            "access_token": app_access_token,
            "refresh_token": app_refresh_token,
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {"id": user.id, "name": user.name, "email": user.email}
        }
    except httpx.HTTPStatusError as e:
        print(f"=== HTTP 에러 ===")
        print(f"Status: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        raise HTTPException(status_code=400, detail=f"Invalid social token: {e.response.text}")
    except Exception as e:
        print(f"=== 일반 에러 ===")
        print(f"Error: {str(e)}")
        print(f"Type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# --- 토큰 갱신 API ---
@router.post("/refresh")
async def refresh_token_endpoint(body: dict = Body(...), db: Session = Depends(get_db)):
    print(f"=== 리프레시 토큰 요청 수신 ===")
    print(f"Request body: {body}")
    
    refresh_token = body.get("refreshToken")
    print(f"Refresh token: {refresh_token}")
    
    if not refresh_token:
        print("=== 에러: 리프레시 토큰 없음 ===")
        raise HTTPException(status_code=401, detail="Refresh token is missing")
    try:
        print(f"=== JWT 디코드 시도 ===")
        print(f"SECRET_KEY: {SECRET_KEY}")
        print(f"ALGORITHM: {ALGORITHM}")
        
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Decoded payload: {payload}")
        
        email = payload.get("sub")
        print(f"Email from token: {email}")
        
        if email is None: 
            print("=== 에러: 토큰에서 이메일 없음 ===")
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user = get_user_by_email(db, email)
        if user is None: 
            print(f"=== 에러: 사용자 없음 - 이메일: {email} ===")
            raise HTTPException(status_code=401, detail="User not found")

        print(f"=== 사용자 발견: {user.email} ===")
        new_access_token = create_access_token(data={"sub": user.email})
        print(f"=== 새 액세스 토큰 생성 완료 ===")
        
        return {
            "access_token": new_access_token,
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except jwt.ExpiredSignatureError:
        print("=== 에러: 리프레시 토큰 만료 ===")
        raise HTTPException(status_code=401, detail="Refresh token has expired")
    except jwt.PyJWTError as e:
        print(f"=== 에러: JWT 에러 - {str(e)} ===")
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    except Exception as e:
        print(f"=== 일반 에러: {str(e)} ===")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
