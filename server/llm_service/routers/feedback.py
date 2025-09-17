"""
피드백 및 학습 관련 API 엔드포인트
사용자 피드백 수집, 프롬프트 성능 분석, 동적 선택 등
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List
from enum import Enum

from ..services.feedback_learning_service import (
    FeedbackLearningService, 
    FeedbackType, 
    FeedbackRating
)
from ..services.dynamic_prompt_selector import DynamicPromptSelector

router = APIRouter(prefix="/feedback", tags=["feedback"])

# Pydantic 모델들
class FeedbackRequest(BaseModel):
    user_id: str
    feedback_type: str  # "community_name", "community_description", "emergency_assessment"
    prompt_used: str
    ai_response: str
    rating: int  # 1-5
    user_comment: Optional[str] = None
    context: Optional[Dict] = None

class PromptSelectionRequest(BaseModel):
    prompt_type: str  # "community_name", "community_description", "emergency_assessment"
    user_context: Dict
    situation_context: Optional[Dict] = None

class PromptAnalysisResponse(BaseModel):
    context_analysis: Dict
    selected_prompt: str
    reason: str

# 서비스 인스턴스
feedback_service = FeedbackLearningService()
prompt_selector = DynamicPromptSelector()

@router.post("/submit")
async def submit_feedback(request: FeedbackRequest):
    """사용자 피드백 수집"""
    try:
        # 피드백 타입 검증
        feedback_type = FeedbackType(request.feedback_type)
        rating = FeedbackRating(request.rating)
        
        feedback_id = await feedback_service.collect_feedback(
            user_id=request.user_id,
            feedback_type=feedback_type,
            prompt_used=request.prompt_used,
            ai_response=request.ai_response,
            rating=rating,
            user_comment=request.user_comment,
            context=request.context
        )
        
        return {
            "success": True,
            "feedback_id": feedback_id,
            "message": "피드백이 성공적으로 수집되었습니다"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"잘못된 피드백 데이터: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"피드백 수집 오류: {str(e)}")

@router.get("/analysis/{feedback_type}")
async def get_feedback_analysis(feedback_type: str):
    """피드백 트렌드 분석"""
    try:
        feedback_type_enum = FeedbackType(feedback_type)
        analysis = await feedback_service.analyze_feedback_trends(feedback_type_enum)
        
        return {
            "success": True,
            "analysis": analysis
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="지원하지 않는 피드백 타입입니다")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 오류: {str(e)}")

@router.post("/prompt/select")
async def select_optimal_prompt(request: PromptSelectionRequest) -> PromptAnalysisResponse:
    """동적 프롬프트 선택"""
    try:
        # 최적 프롬프트 선택
        selected_prompt = await prompt_selector.select_optimal_prompt(
            prompt_type=request.prompt_type,
            user_context=request.user_context,
            situation_context=request.situation_context
        )
        
        # 컨텍스트 분석
        context_analysis = await prompt_selector.get_context_analysis(
            user_context=request.user_context,
            situation_context=request.situation_context or {}
        )
        
        # 선택 이유 생성
        reason = _generate_selection_reason(context_analysis, selected_prompt)
        
        return PromptAnalysisResponse(
            context_analysis=context_analysis,
            selected_prompt=selected_prompt,
            reason=reason
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프롬프트 선택 오류: {str(e)}")

@router.get("/prompt/performance")
async def get_prompt_performance():
    """프롬프트 성능 메트릭 조회"""
    try:
        # 전체 성능 데이터 반환
        performance_data = feedback_service.prompt_performance
        
        # 정렬 및 포맷팅
        sorted_performance = []
        for prompt_key, metrics in performance_data.items():
            prompt_type, prompt_name = prompt_key.split(":", 1)
            sorted_performance.append({
                "prompt_type": prompt_type,
                "prompt_name": prompt_name,
                "average_rating": round(metrics["average_rating"], 2),
                "total_ratings": metrics["total_ratings"],
                "usage_count": metrics["usage_count"]
            })
        
        # 평균 평점으로 정렬
        sorted_performance.sort(key=lambda x: x["average_rating"], reverse=True)
        
        return {
            "success": True,
            "performance_data": sorted_performance,
            "total_prompts": len(sorted_performance)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"성능 데이터 조회 오류: {str(e)}")

@router.post("/prompt/test")
async def test_prompt_selection(request: PromptSelectionRequest):
    """프롬프트 선택 로직 테스트 (개발/디버깅용)"""
    try:
        # 여러 시나리오로 테스트
        test_scenarios = [
            {"name": "현재 요청", "context": request.user_context},
            {"name": "초보 사용자", "context": {**request.user_context, "usage_count": 1}},
            {"name": "숙련 사용자", "context": {**request.user_context, "usage_count": 25}},
        ]
        
        results = []
        for scenario in test_scenarios:
            selected_prompt = await prompt_selector.select_optimal_prompt(
                prompt_type=request.prompt_type,
                user_context=scenario["context"],
                situation_context=request.situation_context
            )
            
            context_analysis = await prompt_selector.get_context_analysis(
                user_context=scenario["context"],
                situation_context=request.situation_context or {}
            )
            
            results.append({
                "scenario": scenario["name"],
                "selected_prompt": selected_prompt,
                "context_analysis": context_analysis
            })
        
        return {
            "success": True,
            "test_results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"테스트 오류: {str(e)}")

def _generate_selection_reason(context_analysis: Dict, selected_prompt: str) -> str:
    """프롬프트 선택 이유 생성"""
    reasons = []
    
    # 경험 레벨 기반 이유
    exp_level = context_analysis.get("user_experience_level")
    if exp_level == "beginner":
        reasons.append("초보 사용자를 위한 친근한 프롬프트")
    elif exp_level == "expert":
        reasons.append("숙련 사용자를 위한 간결한 프롬프트")
    
    # 시간 컨텍스트 기반 이유  
    time_context = context_analysis.get("time_context")
    if time_context == "morning_rush":
        reasons.append("바쁜 아침 시간대를 고려한 빠른 응답")
    elif time_context == "evening_family":
        reasons.append("가족 시간대를 고려한 감성적 접근")
    
    # 지역 기반 이유
    region_type = context_analysis.get("region_type")
    if region_type == "rural":
        reasons.append("시골 지역 특성을 반영한 맞춤형 프롬프트")
    elif region_type == "urban":
        reasons.append("도시 환경에 적합한 실용적 프롬프트")
    
    if not reasons:
        reasons.append("기본 프롬프트 사용")
    
    return " + ".join(reasons)

# 사용 예시 API 호출들:
"""
# 1. 피드백 제출
POST /feedback/submit
{
    "user_id": "user123",
    "feedback_type": "community_name", 
    "prompt_used": "COMMUNITY_NAME_GENERATION",
    "ai_response": "새싹어린이집 모임",
    "rating": 2,
    "user_comment": "너무 딱딱해요",
    "context": {"region": "urban"}
}

# 2. 최적 프롬프트 선택
POST /feedback/prompt/select
{
    "prompt_type": "community_name",
    "user_context": {
        "user_id": "user123",
        "usage_count": 3,
        "location": {"address": "서울시 강남구"}
    }
}

# 3. 피드백 분석 조회
GET /feedback/analysis/community_name

# 4. 프롬프트 성능 조회  
GET /feedback/prompt/performance
"""