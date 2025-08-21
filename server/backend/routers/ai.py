from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import httpx
import os
import datetime
import json

# from ..database import get_db
from ..database_sqlite import get_db
from ..database_sqlite import User as UserModel
from ..models import UserApartment, Child as ChildModel
from ..models import Child
from ..schemas import User
from ..dependencies import get_current_active_user
from ..redis_client import set_cache, get_cache

router = APIRouter(prefix="/ai", tags=["ai-integration"])

# LLM 서비스 설정
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8000")
LLM_SERVICE_API_KEY = os.getenv("LLM_SERVICE_API_KEY", "")

async def get_user_context(user: UserModel, db: Session) -> dict:
    """사용자 컨텍스트 생성"""
    # 사용자 아파트 정보
    user_apartments = db.query(UserApartment).filter(
        UserApartment.user_id == user.id
    ).all()
    user = db.query(UserModel).filter(UserModel.id == user.id).first()
    children = db.query(ChildModel).filter(ChildModel.user_id == user.id).all()

    apartments = []
    for ua in user_apartments:
        apartments.append({
            "id": ua.apartment.id,
            "name": ua.apartment.name,
            "unit_number": ua.unit_number,
            "role": ua.role
        })
    

    user_context = {}  
    children_info = []
    for child in children:
        today = datetime.today().date()
        birth_date = child.birth_date
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        children_info.append({
            "id": child.id,
            "name": child.name,
            "age": age
        })

    user_context = {
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "apartments": apartments,
        "children": children_info
    }
    return user_context
@router.post("/chat")
async def chat_with_ai(
    message: str = Query(..., description="채팅 메시지"),
    mode: str = Query("auto", description="채팅 모드"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    cache_key = f"chat_response:{current_user.id}:{message}:{mode}"
    cached_response = get_cache(cache_key)
    if cached_response:
        return json.loads(cached_response)
    
    try:
        # 사용자 컨텍스트 생성
        user_context = await get_user_context(current_user, db)
        # LLM 서비스 호출
        async with httpx.AsyncClient() as client:
            headers = {}
            if LLM_SERVICE_API_KEY:
                headers["Authorization"] = f"Bearer {LLM_SERVICE_API_KEY}"
            response = await client.post(
                f"{LLM_SERVICE_URL}/chat/unified",
                params={
                    "message": message,
                    "user_id": str(current_user.id),
                    "mode": mode
                },
                json={"user_context": user_context},
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                set_cache(cache_key, json.dumps(result), expire_seconds=300)
                return result
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"LLM 서비스 오류: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="AI 서비스 응답 시간 초과"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI 서비스 연결 오류: {str(e)}"
        )

@router.post("/chat/ai-only")
async def chat_ai_only(
    message: str = Query(..., description="채팅 메시지"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """AI 전용 채팅"""
    return await chat_with_ai(message, "ai_only", current_user, db)

@router.post("/chat/community")
async def chat_community(
    message: str = Query(..., description="채팅 메시지"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """커뮤니티 검색 채팅"""
    return await chat_with_ai(message, "community_only", current_user, db)

@router.get("/chat/history")
async def get_chat_history(
    limit: int = Query(50, description="조회할 메시지 수"),
    current_user: UserModel = Depends(get_current_active_user)
):
    """채팅 히스토리 조회 (LLM 서비스에서)"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {}
            if LLM_SERVICE_API_KEY:
                headers["Authorization"] = f"Bearer {LLM_SERVICE_API_KEY}"
            
            response = await client.get(
                f"{LLM_SERVICE_URL}/chat/history",
                params={
                    "user_id": str(current_user.id),
                    "limit": limit
                },
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"history": [], "message": "히스토리를 불러올 수 없습니다"}
                
    except (httpx.TimeoutException, httpx.RequestError):
        return {"history": [], "message": "히스토리를 불러올 수 없습니다"}

@router.delete("/chat/history")
async def clear_chat_history(
    current_user: UserModel = Depends(get_current_active_user)
):
    """채팅 히스토리 삭제"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {}
            if LLM_SERVICE_API_KEY:
                headers["Authorization"] = f"Bearer {LLM_SERVICE_API_KEY}"
            
            response = await client.delete(
                f"{LLM_SERVICE_URL}/chat/history",
                params={"user_id": str(current_user.id)},
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                return {"message": "채팅 히스토리가 삭제되었습니다"}
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="히스토리 삭제 실패"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="서비스 응답 시간 초과"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"서비스 연결 오류: {str(e)}"
        )

@router.get("/suggestions")
async def get_ai_suggestions(
    context: str = Query("general", description="제안 컨텍스트"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """AI 제안사항 조회"""
    user_context = await get_user_context(current_user, db)
    
    # 간단한 제안사항 (실제로는 LLM 서비스에서 생성)
    suggestions = {
        "general": [
            "오늘 아이 일정을 확인해보세요",
            "우리 아파트 커뮤니티 소식을 확인해보세요",
            "아이의 건강 정보를 업데이트해보세요"
        ],
        "schedule": [
            "다가오는 예방접종 일정이 있나요?",
            "이번 주 놀이 시간을 계획해보세요",
            "아이의 수면 패턴을 기록해보세요"
        ],
        "community": [
            "같은 또래 아이를 키우는 부모들과 소통해보세요",
            "육아 용품 나눔 게시글을 확인해보세요",
            "아파트 내 육아 모임에 참여해보세요"
        ]
    }
    
    return {
        "context": context,
        "suggestions": suggestions.get(context, suggestions["general"]),
        "user_context": user_context
    }
