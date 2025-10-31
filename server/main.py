from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import sys
import json
import firebase_admin
from firebase_admin import credentials
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Backend 라우터들
try:
    from backend.routers.auth import router as auth_router
    from backend.routers.users import router as users_router
    from backend.routers.children import router as children_router
    from backend.routers.ai import router as ai_router
    from backend.routers.alerts import router as alerts_router

    print("✅ Backend 라우터들 import 성공")
except Exception as e:
    print(f"❌ Backend 라우터 import 실패: {e}")
    raise

# LLM Service 라우터들
try:
    from llm_service.routers.chat import router as chat_router
    from llm_service.routers.schedule import router as schedule_router
    from llm_service.routers.location_community import (
        router as location_community_router,
    )
    from llm_service.routers.group_purchase import router as group_purchase_router
    from llm_service.routers.feedback import router as feedback_router

    print("✅ LLM Service 라우터들 import 성공")
except Exception as e:
    print(f"❌ LLM Service 라우터 import 실패: {e}")
    raise

# 환경 변수 로드
load_dotenv()

# Firebase 초기화
cred = None
try:
    # 1순위: 환경변수에서 Firebase Service Account Key 읽기 (Cloud Run용)
    firebase_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    if firebase_key:
        try:
            service_account_info = json.loads(firebase_key)
            cred = credentials.Certificate(service_account_info)
            print("✅ Firebase 환경변수에서 인증정보 로드 성공")
        except json.JSONDecodeError as e:
            print(f"⚠️ Firebase 환경변수 JSON 파싱 실패: {e}")

    if not cred:
        cred_path = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            print("✅ Firebase 로컬 파일에서 인증정보 로드 성공")
        else:
            print(f"⚠️ Firebase Service Account 키 파일을 찾을 수 없습니다: {cred_path}")

    if cred and not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK 초기화 성공!")
    elif not cred:
        print("⚠️ Firebase 인증정보가 없어 Firebase 기능이 비활성화됩니다.")

except Exception as e:
    print(f"⚠️ Firebase Admin SDK 초기화 실패: {e}")

# FastAPI 앱 초기화 (통합)
app = FastAPI(
    title="함께키즈 통합 플랫폼",
    version="2.0.0",
    description="GPS 위치추적과 네이버 지도 API 기반 실제 공동육아 커뮤니티 매칭 플랫폼 (Backend + LLM Service 통합)",
    redirect_slashes=True,
)

print("🏗️ FastAPI 앱 초기화 완료")


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

print("🔗 모든 라우터 등록 완료!")


@app.get("/")
async def root():
    return {
        "message": "함께키즈 통합 플랫폼이 실행 중입니다! (Backend + LLM Service)",
        "timestamp": str(datetime.now()),
    }


@app.get("/health")
async def health_check():
    firebase_status = "connected" if firebase_admin._apps else "disconnected"
    return {
        "status": "healthy",
        "service": "함께키즈 통합 플랫폼",
        "firebase": firebase_status,
        "port": os.getenv("PORT", "8080"),
        "timestamp": str(datetime.now()),
    }


@app.get("/debug")
async def debug_info():
    return {
        "env_port": os.getenv("PORT", "NOT_SET"),
        "cwd": os.getcwd(),
        "firebase_apps": len(firebase_admin._apps) if firebase_admin._apps else 0,
    }


if __name__ == "__main__":
    import uvicorn
    import sys

    port = int(os.getenv("PORT", 8080))
    print(f"🚀 서버 시작 중... 포트: {port}")
    print(f"🐍 Python 버전: {sys.version}")
    print(f"📁 현재 디렉토리: {os.getcwd()}")
    print(f"📝 환경변수 PORT: {os.getenv('PORT', 'NOT_SET')}")

    try:
        uvicorn.run(
            "main:app", host="0.0.0.0", port=port, reload=False, log_level="info"
        )
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
        sys.exit(1)
