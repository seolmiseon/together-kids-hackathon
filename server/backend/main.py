from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, engine
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.children import router as children_router
from routers.ai import router as ai_router
from llm_service.routers.chat import router as chat_router
from llm_service.routers.schedule import router as schedule_router  

# 환경 변수 로드
load_dotenv()


# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 실행
    print("함께키즈 메인 백엔드 서비스 시작")
    yield
    # 종료 시 실행
    print("함께키즈 메인 백엔드 서비스 종료")

# FastAPI 앱 초기화
app = FastAPI(
    title="함께키즈 메인 백엔드 서비스",
    version="1.0.0",
    description="함께키즈 - 아파트 단지 내 맞벌이 부모들의 공동육아 플랫폼",
    lifespan=lifespan
)

# CORS 설정 (프론트엔드 연결용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # Next.js 개발서버
        "http://localhost:3001",    # 추가 개발포트
        "http://127.0.0.1:3000",    # 로컬호스트 대체
        # 배포시 실제 도메인 추가
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# 라우터 등록
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(children_router)
app.include_router(ai_router)


@app.get("/")
async def root():
    return {
        "message": "함께키즈 메인 백엔드 서비스가 실행 중입니다!",
        "service": "main-backend",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    try:
        # DB 연결 테스트
        from database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception as e:
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "함께키즈 메인 백엔드", 
        "database": db_status,
        "llm_service_url": os.getenv("LLM_SERVICE_URL", "http://localhost:8001")
    }
    
    


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
