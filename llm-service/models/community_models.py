from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class HelpRequest(BaseModel):
    """도움 요청 모델"""
    request_id: str
    user_id: str
    title: str
    message: str
    category: str  # "medical", "schedule", "general"
    urgency: str   # "high", "medium", "low"
    image_url: Optional[str] = None
    created_at: datetime = datetime.now()
    status: str = "active"  # "active", "resolved", "closed"


class CommunityResponse(BaseModel):
    """커뮤니티 응답 모델"""
    response_id: str
    request_id: str
    responder_id: str
    message: str
    helpful_count: int = 0
    created_at: datetime = datetime.now()
    is_verified: bool = False  # 신뢰할 수 있는 응답인지


class HelpRequestCreate(BaseModel):
    """도움 요청 생성"""
    title: str
    message: str
    category: str
    urgency: str = "medium"
    image_url: Optional[str] = None


class CommunityResponseCreate(BaseModel):
    """커뮤니티 응답 생성"""
    request_id: str
    message: str


class HelpRequestList(BaseModel):
    """도움 요청 목록"""
    requests: List[HelpRequest]
    total_count: int


class CommunityStats(BaseModel):
    """커뮤니티 통계"""
    active_requests: int
    total_responses: int
    average_response_time: float  # 분 단위
    top_helpers: List[str]
