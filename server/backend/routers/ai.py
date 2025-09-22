from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import httpx
import os
import json
from ..firebase_config import get_firestore_db

from ..schemas import User
from ..dependencies import get_current_user

# Firestore DB 인스턴스 가져오기
def get_db():
    try:
        return get_firestore_db()
    except Exception:
        return None

db = get_db()

router = APIRouter(prefix="/ai", tags=["ai-integration"])

# 통합 서비스 URL (Backend + LLM Service 통합)
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "https://hackathon-integrated-service-529342898795.asia-northeast3.run.app")
LLM_SERVICE_API_KEY = os.getenv("LLM_SERVICE_API_KEY")

def get_user_context(current_user: dict) -> dict:
    uid = current_user.get("uid")
    try:
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
        user_data = user_doc.to_dict() if user_doc.exists else {}

        
        children_ref = db.collection("users").document(uid).collection("children")
        children_docs = children_ref.get()
        children_info = []
        
        # Firestore 날짜 객체를 문자열로 변환
        for child in children_docs:
            child_data = child.to_dict()
            if child_data:
                # 날짜 객체들을 ISO 문자열로 변환
                if 'created_at' in child_data and hasattr(child_data['created_at'], 'isoformat'):
                    child_data['created_at'] = child_data['created_at'].isoformat()
                if 'updated_at' in child_data and hasattr(child_data['updated_at'], 'isoformat'):
                    child_data['updated_at'] = child_data['updated_at'].isoformat()
                    
                children_info.append(child_data)

        user_context = {
            "user_id": uid,
            "user_name": user_data.get("user_name", ""),
            "full_name": user_data.get("full_name", ""),
            "apartments": user_data.get("apartments", []),
            "children": children_info
        }
        return user_context
    except Exception as e:
        print(f"사용자 컨텍스트 생성 중 오류 발생: {e}")
        # 오류 발생 시 최소한의 정보만 반환
        return {"user_id": uid}

@router.post("/chat")
async def chat_with_ai(
    message: str = Query(..., description="채팅 메시지"),
    mode: str = Query("auto", description="채팅 모드"),
    current_user: dict = Depends(get_current_user)
):
   try:
       print(f"=== AI 채팅 요청 시작: {current_user.get('uid')} ===")
       print(f"메시지: {message}")
       
       user_context = get_user_context(current_user)
       print(f"사용자 컨텍스트: {user_context}")

       # 통합 서비스에서는 직접 LLM 라우터 함수 호출
       try:
           from llm_service.routers.chat import unified_chat_endpoint
           from llm_service.models.chat_models import ChatRequest
           print("✅ LLM 모듈 import 성공")
       except ImportError as import_err:
           print(f"❌ LLM 모듈 import 실패: {import_err}")
           raise
       
       # ChatRequest 객체 생성
       try:
           chat_request = ChatRequest(
               user_id=current_user.get("uid"),
               message=message,
               conversation_context={},
               user_context=user_context
           )
           print("✅ ChatRequest 객체 생성 성공")
       except Exception as req_err:
           print(f"❌ ChatRequest 생성 실패: {req_err}")
           raise
       
       print(f"🔄 LLM 라우터 직접 호출 시작...")
       result = await unified_chat_endpoint(chat_request)
       print(f"✅ LLM 라우터 호출 성공")
       
       print(f"LLM 처리 완료")
       return result
            
   except Exception as e:
       import traceback
       error_details = traceback.format_exc()
       print(f"AI 채팅 오류: {str(e)}")
       print(f"상세 오류: {error_details}")
       raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류 발생: {str(e)} | 상세: {error_details[:200]}")

@router.post("/chat/ai-only")
async def chat_ai_only(
    message: str = Query(..., description="채팅 메시지"),
    current_user: dict = Depends(get_current_user)
):
    """AI 전용 채팅"""
    return await chat_with_ai(message, "ai_only", current_user)


@router.post("/chat/community")
async def chat_community(
    message: str = Query(..., description="채팅 메시지"),
    current_user: dict = Depends(get_current_user)
):
    """커뮤니티 검색 채팅"""
    return await chat_with_ai(message, "community_only", current_user)


@router.get("/chat/history")
async def get_chat_history(
    limit: int = Query(50, description="조회할 메시지 수"),
    current_user: dict = Depends(get_current_user)
):
    """채팅 히스토리 조회 (LLM 서비스에서)"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {}
            if LLM_SERVICE_API_KEY:
                headers["Authorization"] = f"Bearer {LLM_SERVICE_API_KEY}"
            
            response = await client.get(
                f"{LLM_SERVICE_URL}/chat/history",
                params={ "user_id": current_user.get("uid"), "limit": limit },
                headers=headers,
                timeout=10.0
            )
            
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"history": [], "message": f"히스토리를 불러올 수 없습니다: {e}"}

@router.delete("/chat/history")
async def clear_chat_history(
    current_user: dict = Depends(get_current_user)
):
    """채팅 히스토리 삭제"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {}
            if LLM_SERVICE_API_KEY:
                headers["Authorization"] = f"Bearer {LLM_SERVICE_API_KEY}"
            
            response = await client.delete(
                f"{LLM_SERVICE_URL}/chat/history",
                params={"user_id": current_user.get("uid")},
                headers=headers,
                timeout=10.0
            )
            
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"히스토리 삭제 실패: {e}")

@router.get("/suggestions")
async def get_ai_suggestions(
    context: str = Query("general", description="제안 컨텍스트"),
    current_user: dict = Depends(get_current_user)
):
    """AI 제안사항 조회"""
    user_context = get_user_context(current_user)
    
    suggestions = {
        "general": ["오늘 아이 일정을 확인해보세요", "우리 아파트 커뮤니티 소식을 확인해보세요"],
        "schedule": ["다가오는 예방접종 일정이 있나요?", "이번 주 놀이 시간을 계획해보세요"],
        "community": ["같은 또래 아이를 키우는 부모들과 소통해보세요", "육아 용품 나눔 게시글을 확인해보세요"]
    }
    
    return {
        "context": context,
        "suggestions": suggestions.get(context, suggestions["general"]),
        "user_context": user_context
    }
