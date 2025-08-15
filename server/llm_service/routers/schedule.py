
from fastapi import APIRouter, HTTPException
from llm_service.services.vector_service import VectorService

router = APIRouter(prefix="/schedule", tags=["schedule"])

# VectorService 인스턴스 (나중에 의존성 주입으로 개선 가능)
vector_service = VectorService()


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
