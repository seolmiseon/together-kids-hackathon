"""
그룹 멤버 조회 서비스

같은 아파트/커뮤니티 멤버를 조회하는 기능을 제공합니다.
"""

import logging
from typing import List, Dict, Any, Optional
from firebase_admin import firestore
import firebase_admin

logger = logging.getLogger(__name__)


class GroupMemberService:
    """그룹 멤버 조회 및 관리 서비스"""
    
    def __init__(self):
        if not firebase_admin._apps:
            try:
                from ...backend.main import cred
                firebase_admin.initialize_app(cred)
            except Exception as e:
                logger.warning(f"Firebase 초기화 실패: {e}")
        
        self.db = firestore.client() if firebase_admin._apps else None
    
    async def get_apartment_members(self, user_id: str, apartment_ids: List[str]) -> List[Dict[str, Any]]:
        """
        같은 아파트 멤버 조회
        
        Args:
            user_id: 현재 사용자 ID
            apartment_ids: 아파트 ID 목록
            
        Returns:
            같은 아파트 멤버 목록 (현재 사용자 제외)
        """
        if not self.db or not apartment_ids:
            return []
        
        try:
            members = []
            # 모든 사용자 조회
            users_ref = self.db.collection("users")
            users_stream = users_ref.stream()
            
            for user_doc in users_stream:
                if user_doc.id == user_id:
                    continue  # 자기 자신 제외
                
                user_data = user_doc.to_dict()
                user_apartments = user_data.get("apartments", [])
                
                # 같은 아파트에 거주하는지 확인
                if any(apt_id in user_apartments for apt_id in apartment_ids):
                    members.append({
                        "user_id": user_doc.id,
                        "full_name": user_data.get("full_name", "알 수 없음"),
                        "user_name": user_data.get("user_name", ""),
                        "apartments": user_apartments
                    })
            
            logger.info(f"아파트 멤버 조회 완료: {len(members)}명")
            return members
            
        except Exception as e:
            logger.error(f"아파트 멤버 조회 실패: {e}")
            return []
    
    async def get_community_members(self, user_id: str, user_location: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """
        같은 커뮤니티 멤버 조회 (위치 기반)
        
        Args:
            user_id: 현재 사용자 ID
            user_location: 사용자 위치 정보 {"lat": float, "lng": float}
            
        Returns:
            같은 커뮤니티 멤버 목록 (현재 사용자 제외)
        """
        if not self.db:
            return []
        
        try:
            # Vector DB에서 커뮤니티 정보 조회는 별도 서비스 사용
            # 여기서는 Firestore의 사용자 위치 기반으로 근처 멤버 조회
            members = []
            
            if not user_location or not user_location.get("lat") or not user_location.get("lng"):
                logger.warning("사용자 위치 정보가 없어 커뮤니티 멤버를 조회할 수 없습니다.")
                return []
            
            user_lat = user_location["lat"]
            user_lng = user_location["lng"]
            
            # 모든 사용자 조회
            users_ref = self.db.collection("users")
            users_stream = users_ref.stream()
            
            for user_doc in users_stream:
                if user_doc.id == user_id:
                    continue  # 자기 자신 제외
                
                user_data = user_doc.to_dict()
                location = user_data.get("location")
                
                if location and location.get("lat") and location.get("lng"):
                    # 거리 계산 (간단한 하버사인 공식)
                    distance = self._calculate_distance(
                        user_lat, user_lng,
                        location["lat"], location["lng"]
                    )
                    
                    # 2km 이내 멤버만 포함 (도보 15분 기준)
                    if distance <= 2000:
                        members.append({
                            "user_id": user_doc.id,
                            "full_name": user_data.get("full_name", "알 수 없음"),
                            "user_name": user_data.get("user_name", ""),
                            "location": location,
                            "distance_meters": distance
                        })
            
            # 거리순 정렬
            members.sort(key=lambda x: x.get("distance_meters", float('inf')))
            
            logger.info(f"커뮤니티 멤버 조회 완료: {len(members)}명")
            return members
            
        except Exception as e:
            logger.error(f"커뮤니티 멤버 조회 실패: {e}")
            return []
    
    async def get_group_members(self, user_id: str, user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        그룹 멤버 통합 조회 (아파트 + 커뮤니티)
        
        Args:
            user_id: 현재 사용자 ID
            user_context: 사용자 컨텍스트 정보
            
        Returns:
            그룹 멤버 목록 (중복 제거)
        """
        members = []
        member_ids = set()
        
        # 1. 같은 아파트 멤버 조회
        apartments = user_context.get("apartments", [])
        if apartments:
            apartment_members = await self.get_apartment_members(user_id, apartments)
            for member in apartment_members:
                if member["user_id"] not in member_ids:
                    members.append(member)
                    member_ids.add(member["user_id"])
        
        # 2. 같은 커뮤니티 멤버 조회 (위치 기반)
        # 사용자 위치 정보 추출
        user_location = None
        children = user_context.get("children", [])
        for child in children:
            if "location" in child:
                user_location = {
                    "lat": child["location"].get("lat"),
                    "lng": child["location"].get("lng")
                }
                break
        
        if user_location:
            community_members = await self.get_community_members(user_id, user_location)
            for member in community_members:
                if member["user_id"] not in member_ids:
                    members.append(member)
                    member_ids.add(member["user_id"])
        
        logger.info(f"통합 그룹 멤버 조회 완료: {len(members)}명")
        return members
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        두 좌표 간 거리 계산 (미터)
        하버사인 공식 사용
        """
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371000  # 지구 반지름 (미터)
        return c * r


# 전역 인스턴스
group_member_service = GroupMemberService()

