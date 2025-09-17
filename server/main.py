from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import credentials

# Backend 라우터들
from backend.routers.auth import router as auth_router
from backend.routers.users import router as users_router
from backend.routers.children import router as children_router
from backend.routers.ai import router as ai_router
from backend.routers.alerts import router as alerts_router

# LLM Service 라우터들  
from llm_service.routers.chat import router as chat_router
from llm_service.routers.schedule import router as schedule_router
from llm_service.routers.location_community import router as location_community_router
from llm_service.routers.group_purchase import router as group_purchase_router
from llm_service.routers.feedback import router as feedback_router

# 환경 변수 로드
load_dotenv()

# Firebase 초기화
try:
    cred_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
    cred = credentials.Certificate(cred_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    print("✅ Firebase Admin SDK 초기화 성공!")
except Exception as e:
    print(f"⚠️ Firebase Admin SDK 초기화 실패: {e}")

# FastAPI 앱 초기화 (통합)
app = FastAPI(
    title="함께키즈 통합 플랫폼",
    version="2.0.0", 
    description="GPS 위치추적과 네이버 지도 API 기반 실제 공동육아 커뮤니티 매칭 플랫폼 (Backend + LLM Service 통합)",
    redirect_slashes=True
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Backend 라우터 등록
app.include_router(auth_router)
app.include_router(users_router) 
app.include_router(children_router)
app.include_router(ai_router)
app.include_router(alerts_router)

# LLM Service 라우터 등록
app.include_router(chat_router)
app.include_router(schedule_router)
app.include_router(location_community_router)
app.include_router(group_purchase_router)
app.include_router(feedback_router)

@app.get("/")
async def root():
    return {"message": "함께키즈 통합 플랫폼이 실행 중입니다! (Backend + LLM Service)"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "함께키즈 통합 플랫폼"}