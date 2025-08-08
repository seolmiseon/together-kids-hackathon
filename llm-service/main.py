from fastapi import FastAPI
from dotenv import load_dotenv
import os

from routers import chat, schedule

# 환경 변수 로드P
load_dotenv()

# FastAPI 앱 초기화
app = FastAPI(
    title="함께키즈 AI 챗봇 서비스",
    version="1.0.0",
    description="아파트 단지 내 맞벌이 부모들의 공동육아를 돕는 AI 챗봇"
)

# 라우터 등록
app.include_router(chat.router)
app.include_router(schedule.router)


@app.get("/")
async def root():
    return {"message": "함께키즈 AI 챗봇 서비스가 실행 중입니다!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "함께키즈 AI"}

@app.get("/env-test")
async def env_test():
    database_url = os.getenv("DATABASE_URL")
    secret_key = os.getenv("SECRET_KEY")
    return {
        "DATABASE_URL": database_url,
        "SECRET_KEY": "****" if secret_key else None 
    }
