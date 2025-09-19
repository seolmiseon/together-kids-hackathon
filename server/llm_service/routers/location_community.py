"""
GPS 위치 기반 공동육아 API
실제 위치추적과 네이버 지도 API를 활용한 진짜 커뮤니티 매칭
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging
import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ..services.real_community_service import real_community_service
from ..services.location_service import location_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/location", tags=["위치기반커뮤니티"])

class UserLocation(BaseModel):
    latitude: float
    longitude: float
    address: Optional[str] = None

class UserProfile(BaseModel):
    user_id: str
    child_ages: List[str]
    parenting_style: List[str]
    interests: List[str]
    location: UserLocation

class CommunityRequest(BaseModel):
    user_profile: UserProfile
    community_type: str  # same_apartment, same_daycare, same_playground, neighborhood, working_parents

class JoinCommunityRequest(BaseModel):
    community_id: str
    user_id: str

@router.post("/check-area")
async def check_supported_area(location: UserLocation):
    """
    사용자 위치가 유효한 GPS 좌표인지 확인 (전국 서비스)
    """
    try:
        # GPS 좌표 유효성 확인
        is_valid = location_service.is_location_valid(
            location.latitude, location.longitude
        )
        
        if not is_valid:
            return {
                "supported": False,
                "message": "유효하지 않은 GPS 좌표입니다."
            }
        
        # 주소 정보 가져오기
        address_info = await location_service.reverse_geocode(
            location.latitude, location.longitude
        )
        
        return {
            "supported": True,
            "address_info": address_info,
            "message": "전국 어디서든 공동육아 서비스를 이용할 수 있습니다!"
        }
        
    except Exception as e:
        logger.error(f"지역 확인 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="지역 확인 중 오류가 발생했습니다")

@router.post("/nearby-communities")
async def find_nearby_communities(user_location: UserLocation, max_distance_minutes: int = 15):
    """
    사용자 위치 기반 근처 커뮤니티 찾기
    """
    try:
        # GPS 좌표 유효성 확인
        is_valid = location_service.is_location_valid(
            user_location.latitude, user_location.longitude
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=400, 
                detail="유효하지 않은 GPS 좌표입니다."
            )
        
        # 주소 정보 추가
        if not user_location.address:
            address_info = await location_service.reverse_geocode(
                user_location.latitude, user_location.longitude
            )
            user_location.address = address_info.get("address", "") if address_info else ""
        
        location_dict = {
            "latitude": user_location.latitude,
            "longitude": user_location.longitude,
            "address": user_location.address
        }
        
        # 근처 커뮤니티 찾기
        nearby_communities = await real_community_service.find_nearby_communities(
            location_dict, max_distance_minutes
        )
        
        return {
            "user_location": user_location.address,
            "search_radius_minutes": max_distance_minutes,
            "communities_found": len(nearby_communities),
            "communities": nearby_communities
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"근처 커뮤니티 검색 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="커뮤니티 검색 중 오류가 발생했습니다")

@router.post("/create-community")
async def create_location_based_community(request: CommunityRequest):
    """
    사용자 위치 기반 커뮤니티 생성
    """
    try:
        # 지원 지역 확인
        is_supported, area_name = location_service.is_location_supported(
            request.user_profile.location.latitude,
            request.user_profile.location.longitude
        )
        
        if not is_supported:
            raise HTTPException(
                status_code=400,
                detail="지원하지 않는 지역입니다. 의정부시, 구리시, 도봉구, 노원구만 서비스됩니다."
            )
        
        # 주소 정보 추가
        location_dict = {
            "latitude": request.user_profile.location.latitude,
            "longitude": request.user_profile.location.longitude,
            "address": request.user_profile.location.address or ""
        }
        
        if not location_dict["address"]:
            address_info = await location_service.reverse_geocode(
                location_dict["latitude"], location_dict["longitude"]
            )
            location_dict["address"] = address_info.get("address", "") if address_info else ""
        
        # 사용자 프로필 변환
        user_profile_dict = {
            "user_id": request.user_profile.user_id,
            "child_ages": request.user_profile.child_ages,
            "parenting_style": request.user_profile.parenting_style,
            "interests": request.user_profile.interests
        }
        
        # 커뮤니티 생성
        community_id = await real_community_service.create_and_add_community(
            location_dict, request.community_type, user_profile_dict
        )
        
        if not community_id:
            raise HTTPException(status_code=500, detail="커뮤니티 생성에 실패했습니다")
        
        return {
            "success": True,
            "community_id": community_id,
            "area": area_name,
            "message": f"{area_name}에 새로운 공동육아 커뮤니티가 생성되었습니다!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"커뮤니티 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="커뮤니티 생성 중 오류가 발생했습니다")

@router.post("/join-community")
async def join_community(request: JoinCommunityRequest):
    """
    커뮤니티 가입
    """
    try:
        success = await real_community_service.join_community(
            request.community_id, request.user_id
        )
        
        if success:
            return {
                "success": True,
                "message": "커뮤니티에 성공적으로 가입했습니다!"
            }
        else:
            raise HTTPException(status_code=400, detail="커뮤니티 가입에 실패했습니다")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"커뮤니티 가입 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="커뮤니티 가입 중 오류가 발생했습니다")

@router.get("/community-types")
async def get_community_types():
    """
    사용 가능한 커뮤니티 유형 목록
    """
    return {
        "community_types": [
            {
                "type": "same_apartment",
                "name": "같은 아파트 품앗이",
                "description": "같은 아파트 단지 거주민들의 공동육아",
                "max_distance": "단지 내 5분 이내"
            },
            {
                "type": "same_daycare",
                "name": "같은 어린이집 학부모",
                "description": "같은 어린이집을 다니는 아이들의 부모",
                "max_distance": "어린이집 주변 10분 이내"
            },
            {
                "type": "same_playground",
                "name": "같은 놀이터 엄마들",
                "description": "같은 놀이터를 이용하는 부모들",
                "max_distance": "놀이터 주변 10분 이내"
            },
            {
                "type": "neighborhood",
                "name": "동네 육아 모임",
                "description": "같은 동네에서 육아하는 부모들",
                "max_distance": "도보 15분 이내"
            },
            {
                "type": "working_parents",
                "name": "워킹맘/워킹대디",
                "description": "직장 다니는 부모들의 긴급돌봄",
                "max_distance": "20분 이내"
            }
        ]
    }

@router.get("/nearby")
async def get_nearby_communities_simple(
    lat: float = Query(..., description="위도"),
    lon: float = Query(..., description="경도"), 
    distance: int = Query(15, description="최대 거리 (분)")
):
    """
    프론트엔드에서 쉽게 사용할 수 있는 간단한 근처 커뮤니티 API
    GET /location/nearby?lat=37.5663&lon=126.9779&distance=15
    """
    try:
        # GPS 좌표 유효성 확인
        is_valid = location_service.is_location_valid(lat, lon)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="유효하지 않은 GPS 좌표입니다")
        
        # 주소 정보 가져오기
        address_info = await location_service.reverse_geocode(lat, lon)
        address = address_info.get("address", "") if address_info else ""
        
        location_dict = {
            "latitude": lat,
            "longitude": lon,
            "address": address
        }
        
        # 근처 커뮤니티 찾기
        nearby_communities = await real_community_service.find_nearby_communities(
            location_dict, distance
        )
        
        return {
            "success": True,
            "user_location": {
                "latitude": lat,
                "longitude": lon,
                "address": address
            },
            "search_distance_minutes": distance,
            "total_found": len(nearby_communities),
            "communities": nearby_communities
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"근처 커뮤니티 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="근처 커뮤니티 조회 중 오류가 발생했습니다")

@router.get("/distance")
async def calculate_distance_simple(
    lat1: float = Query(..., description="시작점 위도"),
    lon1: float = Query(..., description="시작점 경도"),
    lat2: float = Query(..., description="도착점 위도"), 
    lon2: float = Query(..., description="도착점 경도")
):
    """
    두 지점 간 거리 계산 (프론트엔드용 간단 API)
    GET /location/distance?lat1=37.5663&lon1=126.9779&lat2=37.4979&lon2=127.0276
    """
    try:
        distance_meters = location_service.calculate_distance(lat1, lon1, lat2, lon2)
        walking_minutes = location_service.calculate_walking_time(distance_meters)
        driving_minutes = location_service.calculate_driving_time(distance_meters)
        
        return {
            "success": True,
            "distance": {
                "meters": round(distance_meters, 1),
                "kilometers": round(distance_meters / 1000, 2)
            },
            "travel_time": {
                "walking_minutes": walking_minutes,
                "driving_minutes": driving_minutes
            },
            "within_walking_15min": walking_minutes <= 15,
            "within_driving_15min": driving_minutes <= 15
        }
        
    except Exception as e:
        logger.error(f"거리 계산 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="거리 계산 중 오류가 발생했습니다")
