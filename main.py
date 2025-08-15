from fastapi import FastAPI
from .server.backend.routers import auth as auth_router
from .server.backend.routers import users as users_router
from .server.backend.routers import children as children_router
from .server.backend.routers import ai as ai_router
from .server.llm_service.routers import chat as chat_router
from .server.llm_service.routers import schedule as schedule_router

app = FastAPI(
    title="함께키즈 통합 서버",
    version="1.0.0",
    description="백엔드와 LLM 서비스 통합 FastAPI 서버"
)

# 백엔드 라우터 등록 (prefix는 필요에 따라 조정 가능)
app.include_router(auth_router.router, prefix="/backend/auth")
app.include_router(users_router.router, prefix="/backend/users")
app.include_router(children_router.router, prefix="/backend/children")
app.include_router(ai_router.router, prefix="/backend/ai")

# LLM 서비스 라우터 등록
app.include_router(chat_router.router, prefix="/llm/chat")
app.include_router(schedule_router.router, prefix="/llm/schedule")

# 간단 상태 확인용 엔드포인트
@app.get("/backend/status")
async def backend_status():
    return {"status": "백엔드 정상 작동 중"}

@app.get("/llm/status")
async def llm_status():
    return {"status": "LLM 서비스 정상 작동 중"}

@app.get("/")
async def root():
    return {"message": "함께키즈 통합 서버 실행 중!"}
