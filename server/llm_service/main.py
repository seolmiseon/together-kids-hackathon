from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError
from dotenv import load_dotenv
import logging

from .routers import chat, schedule, location_community, group_purchase

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title="함께키즈 GPS 기반 공동육아 플랫폼",
    version="2.0.0",
    description="GPS 위치추적과 네이버 지도 API 기반 실제 공동육아 커뮤니티 매칭 플랫폼"
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
app.include_router(location_community.router)  # GPS 위치 기반 커뮤니티 API
app.include_router(group_purchase.router)      # 공동구매 및 나눔 API


@app.get("/")
async def root():
    return {"message": "함께키즈 GPS 기반 공동육아 플랫폼이 실행 중입니다!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "함께키즈 위치기반 커뮤니티"}
    
# 전역 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
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
    
