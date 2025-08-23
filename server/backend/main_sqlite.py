from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 환경변수 로드 (최상위에서 한 번만)
load_dotenv()

from .database_sqlite import create_tables


from .routers import auth, users, children, alerts,ai
from llm_service.routers import chat as llm_chat
from llm_service.routers import schedule as llm_schedule


app = FastAPI(
    title="함께 키즈 API (SQLite)", 
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# [수정] 가져온 모든 라우터를 FastAPI 앱에 등록합니다.
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(children.router)
app.include_router(alerts.router)
app.include_router(ai.router)
app.include_router(llm_chat.router)
app.include_router(llm_schedule.router)


# 시작 시 테이블 생성
@app.on_event("startup")
async def startup_event():
    create_tables()
    print("🚀 함께 키즈 SQLite 서버 시작!")

# 기본 엔드포인트
@app.get("/")
async def root():
    return {"message": "함께 키즈 API (SQLite 버전)", "status": "running"}
