"""
공동구매 및 나눔 API
⭐⭐ 기저귀, 장난감, 육아용품 공동구매 및 나눔 REST API
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging
import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.group_purchase_service import group_purchase_service, ShareType, ItemCategory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/share", tags=["공동구매및나눔"])

class LocationData(BaseModel):
    latitude: float
    longitude: float
    address: str

class CreateGroupPurchaseRequest(BaseModel):
    title: str
    description: str
    category: ItemCategory
    target_quantity: int
    price_per_unit: float
    total_price: float
    location: LocationData
    pickup_location: str
    deadline: Optional[str] = None
    images: List[str] = []
    requirements: str = ""
    contact_method: str = "앱 내 메시지"

class CreateSharingItemRequest(BaseModel):
    title: str
    description: str
    category: ItemCategory
    share_type: ShareType
    condition: str = "보통"
    original_price: float = 0
    sharing_price: float = 0
    location: LocationData
    pickup_location: str
    available_until: Optional[str] = None
    images: List[str] = []
    age_range: str = ""
    brand: str = ""
    contact_method: str = "앱 내 메시지"
    # 대여용 추가 필드
    rental_period: Optional[str] = None
    deposit: Optional[float] = None

class JoinGroupPurchaseRequest(BaseModel):
    item_id: str
    user_id: str
    quantity: int = 1

class ExpressInterestRequest(BaseModel):
    item_id: str
    user_id: str

@router.post("/group-purchase")
async def create_group_purchase(request: CreateGroupPurchaseRequest, creator_id: str = Query(...)):
    """
    공동구매 생성
    """
    try:
        item_data = {
            "title": request.title,
            "description": request.description,
            "category": request.category,
            "target_quantity": request.target_quantity,
            "price_per_unit": request.price_per_unit,
            "total_price": request.total_price,
            "location": {
                "latitude": request.location.latitude,
                "longitude": request.location.longitude,
                "address": request.location.address
            },
            "pickup_location": request.pickup_location,
            "deadline": request.deadline,
            "images": request.images,
            "requirements": request.requirements,
            "contact_method": request.contact_method
        }
        
        item_id = group_purchase_service.create_group_purchase(creator_id, item_data)
        
        if not item_id:
            raise HTTPException(status_code=500, detail="공동구매 생성에 실패했습니다")
        
        return {
            "success": True,
            "item_id": item_id,
            "message": "공동구매가 성공적으로 생성되었습니다!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"공동구매 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="공동구매 생성 중 오류가 발생했습니다")

@router.post("/sharing-item")
async def create_sharing_item(request: CreateSharingItemRequest, creator_id: str = Query(...)):
    """
    나눔/교환/대여 아이템 생성
    """
    try:
        item_data = {
            "title": request.title,
            "description": request.description,
            "category": request.category,
            "share_type": request.share_type,
            "condition": request.condition,
            "original_price": request.original_price,
            "sharing_price": request.sharing_price,
            "location": {
                "latitude": request.location.latitude,
                "longitude": request.location.longitude,
                "address": request.location.address
            },
            "pickup_location": request.pickup_location,
            "available_until": request.available_until,
            "images": request.images,
            "age_range": request.age_range,
            "brand": request.brand,
            "contact_method": request.contact_method
        }
        
        # 대여용 추가 정보
        if request.share_type == ShareType.RENTAL:
            item_data.update({
                "rental_period": request.rental_period,
                "deposit": request.deposit
            })
        
        item_id = group_purchase_service.create_sharing_item(creator_id, item_data)
        
        if not item_id:
            raise HTTPException(status_code=500, detail="아이템 생성에 실패했습니다")
        
        share_type_names = {
            ShareType.SHARING: "나눔",
            ShareType.EXCHANGE: "교환", 
            ShareType.RENTAL: "대여"
        }
        
        return {
            "success": True,
            "item_id": item_id,
            "message": f"{share_type_names.get(request.share_type, '아이템')}이 성공적으로 등록되었습니다!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"아이템 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="아이템 생성 중 오류가 발생했습니다")

@router.post("/join-group-purchase")
async def join_group_purchase(request: JoinGroupPurchaseRequest):
    """
    공동구매 참여
    """
    try:
        success = group_purchase_service.join_group_purchase(
            request.item_id, request.user_id, request.quantity
        )
        
        if success:
            return {
                "success": True,
                "message": "공동구매에 성공적으로 참여했습니다!"
            }
        else:
            raise HTTPException(status_code=400, detail="공동구매 참여에 실패했습니다")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"공동구매 참여 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="공동구매 참여 중 오류가 발생했습니다")

@router.post("/express-interest")
async def express_interest(request: ExpressInterestRequest):
    """
    나눔 아이템에 관심 표현
    """
    try:
        success = group_purchase_service.express_interest(request.item_id, request.user_id)
        
        if success:
            return {
                "success": True,
                "message": "관심 표현을 완료했습니다!"
            }
        else:
            raise HTTPException(status_code=400, detail="관심 표현에 실패했습니다")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"관심 표현 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="관심 표현 중 오류가 발생했습니다")

@router.get("/search")
async def search_items(
    category: Optional[ItemCategory] = None,
    share_type: Optional[ShareType] = None,
    keyword: Optional[str] = None,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    user_address: Optional[str] = None,
    max_distance_km: float = 5.0
):
    """
    아이템 검색
    """
    try:
        user_location = None
        if user_lat and user_lon:
            user_location = {
                "latitude": user_lat,
                "longitude": user_lon,
                "address": user_address or ""
            }
        
        items = group_purchase_service.search_items(
            user_location=user_location,
            category=category,
            share_type=share_type,
            max_distance_km=max_distance_km,
            keyword=keyword
        )
        
        return {
            "items": items,
            "total_count": len(items),
            "search_params": {
                "category": category,
                "share_type": share_type,
                "keyword": keyword,
                "max_distance_km": max_distance_km
            }
        }
        
    except Exception as e:
        logger.error(f"아이템 검색 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="아이템 검색 중 오류가 발생했습니다")

@router.get("/my-items")
async def get_my_items(user_id: str = Query(...)):
    """
    내 아이템 목록 조회
    """
    try:
        my_items = group_purchase_service.get_my_items(user_id)
        
        return {
            "my_items": my_items,
            "summary": {
                "created_count": len(my_items["created"]),
                "participated_count": len(my_items["participated"]),
                "interested_count": len(my_items["interested"])
            }
        }
        
    except Exception as e:
        logger.error(f"내 아이템 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="내 아이템 조회 중 오류가 발생했습니다")

@router.get("/categories")
async def get_categories():
    """
    사용 가능한 카테고리 목록
    """
    categories = [
        {"value": "diapers", "name": "기저귀", "icon": "🍼"},
        {"value": "baby_food", "name": "이유식/유아식품", "icon": "🥄"},
        {"value": "toys", "name": "장난감", "icon": "🧸"},
        {"value": "clothes", "name": "아동복", "icon": "👶"},
        {"value": "books", "name": "도서", "icon": "📚"},
        {"value": "furniture", "name": "아동 가구", "icon": "🪑"},
        {"value": "stroller", "name": "유모차", "icon": "🚼"},
        {"value": "car_seat", "name": "카시트", "icon": "🚗"},
        {"value": "feeding", "name": "수유용품", "icon": "🍼"},
        {"value": "bath", "name": "목욕용품", "icon": "🛁"},
        {"value": "educational", "name": "교육용품", "icon": "🎓"},
        {"value": "outdoor", "name": "야외활동용품", "icon": "⛰️"}
    ]
    
    return {"categories": categories}

@router.get("/share-types")
async def get_share_types():
    """
    사용 가능한 공유 유형 목록
    """
    share_types = [
        {
            "value": "group_purchase", 
            "name": "공동구매", 
            "description": "함께 구매해서 배송비와 비용을 절약해요",
            "icon": "🛒"
        },
        {
            "value": "sharing", 
            "name": "나눔", 
            "description": "더 이상 사용하지 않는 물건을 나눠드려요",
            "icon": "💝"
        },
        {
            "value": "exchange", 
            "name": "교환", 
            "description": "서로 필요한 물건을 교환해요",
            "icon": "🔄"
        },
        {
            "value": "rental", 
            "name": "대여", 
            "description": "잠깐 필요한 물건을 빌려드려요",
            "icon": "📅"
        }
    ]
    
    return {"share_types": share_types}

@router.get("/popular-categories")
async def get_popular_categories():
    """
    인기 카테고리 조회
    """
    try:
        popular_categories = group_purchase_service.get_popular_categories()
        
        return {
            "popular_categories": popular_categories,
            "total_categories": len(popular_categories)
        }
        
    except Exception as e:
        logger.error(f"인기 카테고리 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="인기 카테고리 조회 중 오류가 발생했습니다")
