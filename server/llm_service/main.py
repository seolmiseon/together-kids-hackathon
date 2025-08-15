from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import HTTPException
from llm_service.utils.chunk_utils import split_text_by_meaning
from llm_service.services.vector_service import VectorService
import asyncio
from dotenv import load_dotenv
import os
import logging
from llm_service.routers import chat, schedule
import pandas as pd

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title="함께키즈 AI 챗봇 서비스",
    version="1.0.0",
    description="아파트 단지 내 맞벌이 부모들의 공동육아를 돕는 AI 챗봇"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    
# 전역 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "서버 내부 오류가 발생했습니다."},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )
    
async def initialize_vector_store_from_csv(csv_path):
    df = pd.read_csv(csv_path)
    vector_service = VectorService()
    for idx, row in df.iterrows():
        chunks = split_text_by_meaning(row['text'])
        for chunk in chunks:
            await vector_service.add_schedule_info(user_id=row['user_id'], schedule_text=chunk)
    
    
if __name__ == "__main__":
    import uvicorn
    asyncio.run(initialize_vector_store_from_csv("mydata.csv"))
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)    