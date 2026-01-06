
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from pydantic import BaseModel
from llm_service.services.vector_service import VectorService
from llm_service.services.rsvp_service import rsvp_service

router = APIRouter(prefix="/schedule", tags=["schedule"])

# VectorService 인스턴스 (나중에 의존성 주입으로 개선 가능)
vector_service = VectorService()


class RSVPRequest(BaseModel):
    """RSVP 응답 요청 모델"""
    schedule_id: str
    user_id: str
    response: str  # "attending", "not_attending", "maybe"


@router.post("/")
async def add_schedule(user_id: str, schedule_text: str):
    """스케줄 정보 추가"""
    try:
        await vector_service.add_schedule_info(user_id, schedule_text)
        return {"message": f"{user_id}의 스케줄이 저장되었습니다: {schedule_text}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄 저장 중 오류가 발생했습니다: {str(e)}")


@router.get("/search")
async def search_schedules(query: str):
    """스케줄 검색 테스트"""
    try:
        results = await vector_service.search_similar_schedules(query)
        return {"query": query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄 검색 중 오류가 발생했습니다: {str(e)}")


@router.post("/rsvp")
async def submit_rsvp(request: RSVPRequest):
    """
    RSVP 응답 제출
    
    - schedule_id: 일정 ID
    - user_id: 사용자 ID
    - response: 응답 ("attending", "not_attending", "maybe")
    """
    try:
        result = await rsvp_service.submit_rsvp(
            schedule_id=request.schedule_id,
            user_id=request.user_id,
            response=request.response
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "RSVP 응답 저장 실패"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RSVP 응답 저장 중 오류가 발생했습니다: {str(e)}")


@router.get("/rsvp/{schedule_id}")
async def get_rsvp_status(schedule_id: str):
    """
    일정의 RSVP 상태 조회
    
    - schedule_id: 일정 ID
    """
    try:
        result = await rsvp_service.get_schedule_rsvp_status(schedule_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message", "일정을 찾을 수 없습니다."))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RSVP 상태 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/rsvp/user/{user_id}")
async def get_user_rsvp_schedules(user_id: str):
    """
    사용자가 응답한 모든 RSVP 일정 조회
    
    - user_id: 사용자 ID
    """
    try:
        schedules = await rsvp_service.get_user_rsvp_status(user_id)
        return {"user_id": user_id, "schedules": schedules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 RSVP 일정 조회 중 오류가 발생했습니다: {str(e)}")
