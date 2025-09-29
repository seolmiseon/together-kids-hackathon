"""
위치 기반 서비스 - 네이버 지도 API 연동
GPS 위치추적, 거리계산, 실제 지역 기반 커뮤니티 매칭
"""

import requests
import math
import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

class LocationService:
    def __init__(self):
        # 네이버 지도 API 키
        self.naver_client_id = os.getenv("NAVER_MAP_CLIENT_ID")
        self.naver_client_secret = os.getenv("NAVER_MAP_CLIENT_SECRET")
        
        # 거리 기반 서비스 설정 (지역 제한 없음)
        self.max_service_radius_km = 50  # 최대 서비스 반경 50km (합리적 제한)
        
    def is_location_valid(self, latitude: float, longitude: float) -> bool:
        """
        위치가 유효한 GPS 좌표인지 확인 (지역 제한 없음)
        
        Args:
            latitude: 위도
            longitude: 경도
            
        Returns:
            유효한 GPS 좌표인지 여부
        """
        # 기본적인 GPS 좌표 유효성만 체크
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return False
        
        # 대한민국 대략적 범위 체크 (너무 넓게)
        korea_bounds = {
            "north": 38.6,   # 북한 경계 근처
            "south": 33.0,   # 제주도 남쪽
            "east": 132.0,   # 울릉도 동쪽  
            "west": 124.0    # 서해 서쪽
        }
        
        return (korea_bounds["south"] <= latitude <= korea_bounds["north"] and 
                korea_bounds["west"] <= longitude <= korea_bounds["east"])
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        두 GPS 좌표 간의 거리 계산 (하버사인 공식)
        
        Args:
            lat1, lon1: 첫 번째 위치의 위도, 경도
            lat2, lon2: 두 번째 위치의 위도, 경도
            
        Returns:
            거리 (미터)
        """
        # 지구 반지름 (미터)
        R = 6371000
        
        # 라디안으로 변환
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # 하버사인 공식
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        distance = R * c
        return distance
    
    def calculate_walking_time(self, distance_meters: float) -> int:
        """
        도보 이동 시간 계산 (분)
        평균 도보 속도: 4km/h = 67m/min
        
        Args:
            distance_meters: 거리 (미터)
            
        Returns:
            도보 시간 (분)
        """
        walking_speed_m_per_min = 67  # 67m/분
        walking_time_minutes = distance_meters / walking_speed_m_per_min
        return int(walking_time_minutes)
    
    def calculate_driving_time(self, distance_meters: float) -> int:
        """
        차량 이동 시간 계산 (분)
        평균 시내 차량 속도: 30km/h = 500m/min (신호등, 교통체증 고려)
        
        Args:
            distance_meters: 거리 (미터)
            
        Returns:
            차량 이동 시간 (분)
        """
        driving_speed_m_per_min = 500  # 500m/분 (30km/h)
        driving_time_minutes = distance_meters / driving_speed_m_per_min
        return int(driving_time_minutes)
    
    def is_within_distance(self, lat1: float, lon1: float, lat2: float, lon2: float, 
                          max_minutes: int = 15, transport_type: str = "walking") -> bool:
        """
        지정된 이동 시간 이내 거리인지 확인
        
        Args:
            lat1, lon1: 첫 번째 위치
            lat2, lon2: 두 번째 위치
            max_minutes: 최대 이동 시간 (분)
            transport_type: 이동 수단 ("walking" 또는 "driving")
            
        Returns:
            지정 시간 내 이동 가능 여부
        """
        distance = self.calculate_distance(lat1, lon1, lat2, lon2)
        
        if transport_type == "walking":
            travel_time = self.calculate_walking_time(distance)
        elif transport_type == "driving":
            travel_time = self.calculate_driving_time(distance)
        else:
            raise ValueError("transport_type은 'walking' 또는 'driving'이어야 합니다")
            
        return travel_time <= max_minutes
    
    async def geocode_address(self, address: str) -> Optional[Dict]:
        """
        주소를 GPS 좌표로 변환 (네이버 지도 API)
        
        Args:
            address: 주소
            
        Returns:
            {"latitude": float, "longitude": float, "address": str}
        """
        if not self.naver_client_id or not self.naver_client_secret:
            logger.error("네이버 지도 API 키가 설정되지 않았습니다")
            return None
            
        try:
            url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
            headers = {
                "X-NCP-APIGW-API-KEY-ID": self.naver_client_id,
                "X-NCP-APIGW-API-KEY": self.naver_client_secret
            }
            params = {"query": address}
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data["addresses"]:
                    result = data["addresses"][0]
                    return {
                        "latitude": float(result["y"]),
                        "longitude": float(result["x"]),
                        "address": result["roadAddress"] or result["jibunAddress"]
                    }
            
            logger.error(f"Geocoding 실패: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Geocoding 오류: {str(e)}")
            return None
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        GPS 좌표를 주소로 변환 (네이버 지도 API)
        
        Args:
            latitude: 위도
            longitude: 경도
            
        Returns:
            {"address": str, "district": str, "area": str}
        """
        if not self.naver_client_id or not self.naver_client_secret:
            logger.error("네이버 지도 API 키가 설정되지 않았습니다")
            return None
            
        try:
            url = "https://naveropenapi.apigw.ntruss.com/map-reversegeocode/v2/gc"
            headers = {
                "X-NCP-APIGW-API-KEY-ID": self.naver_client_id,
                "X-NCP-APIGW-API-KEY": self.naver_client_secret
            }
            params = {
                "coords": f"{longitude},{latitude}",
                "sourcecrs": "epsg:4326",
                "targetcrs": "epsg:4326",
                "output": "json"
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data["status"]["code"] == 0 and data["results"]:
                    region = data["results"][0]["region"]
                    
                    # 시/구 정보 추출
                    area1 = region.get("area1", {}).get("name", "")  # 시/도
                    area2 = region.get("area2", {}).get("name", "")  # 시/군/구
                    area3 = region.get("area3", {}).get("name", "")  # 동/읍/면
                    
                    return {
                        "address": f"{area1} {area2} {area3}",
                        "district": area3,
                        "area": area2
                    }
            
            logger.error(f"Reverse Geocoding 실패: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Reverse Geocoding 오류: {str(e)}")
            return None
    async def search_nearby_places(self, keyword: str, latitude: float, longitude: float, radius: int = 1000) -> List[Dict]:
        """
        주변 장소 검색 (네이버 지역검색 API)
        
        Args:
            keyword: 검색 키워드 (예: "놀이터", "키즈카페")
            latitude: 위도
            longitude: 경도
            radius: 검색 반경 (미터, 기본 1km)
            
        Returns:
            장소 리스트 [{"name": str, "address": str, "telephone": str, "description": str}, ...]
        """
        if not self.naver_client_id or not self.naver_client_secret:
            logger.error("네이버 지도 API 키가 설정되지 않았습니다")
            return []
            
        try:
            # 네이버 지역검색 API
            url = "https://openapi.naver.com/v1/search/local.json"
            headers = {
                "X-Naver-Client-Id": self.naver_client_id,
                "X-Naver-Client-Secret": self.naver_client_secret
            }
            
            # 좌표 기반 검색을 위한 쿼리 구성
            search_query = f"{keyword}"
            params = {
                "query": search_query,
                "display": 10,  # 최대 10개 결과
                "start": 1,
                "sort": "random"  # 거리순 정렬은 좌표 없이는 어려움
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                places = []
                
                for item in data.get("items", []):
                    # HTML 태그 제거
                    name = item.get("title", "").replace("<b>", "").replace("</b>", "")
                    address = item.get("address", "")
                    telephone = item.get("telephone", "")
                    description = item.get("description", "")
                    
                    # 기본 정보가 있는 경우만 추가
                    if name and address:
                        place_info = {
                            "name": name,
                            "address": address,
                            "telephone": telephone,
                            "description": description,
                            "naver_map_url": f"https://map.naver.com/v5/search/{address}",
                            "naver_app_url": f"nmap://search?query={address}",  
                            "google_maps_url": f"https://maps.google.com/maps?q={address}",
                            "kakao_map_url": f"https://map.kakao.com/link/search/{address}"
                        }
                        places.append(place_info)
                
                logger.info(f"'{keyword}' 검색 결과: {len(places)}개")
                return places
            else:
                logger.error(f"장소 검색 실패: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"장소 검색 오류: {str(e)}")
            return []    
    
    def find_nearby_locations(self, user_lat: float, user_lon: float, locations: List[Dict], max_distance_minutes: int = 15) -> List[Dict]:
        """
        사용자 주변의 위치들을 찾기
        
        Args:
            user_lat, user_lon: 사용자 위치
            locations: 검색할 위치 목록 [{"latitude": float, "longitude": float, "data": dict}, ...]
            max_distance_minutes: 최대 거리 (분)
            
        Returns:
            거리순으로 정렬된 근처 위치 목록
        """
        nearby_locations = []
        
        for location in locations:
            if "latitude" not in location or "longitude" not in location:
                continue
                
            distance_meters = self.calculate_distance(
                user_lat, user_lon,
                location["latitude"], location["longitude"]
            )
            walking_minutes = self.calculate_walking_time(distance_meters)
            
            if walking_minutes <= max_distance_minutes:
                location_with_distance = location.copy()
                location_with_distance.update({
                    "distance_meters": distance_meters,
                    "walking_minutes": walking_minutes
                })
                nearby_locations.append(location_with_distance)
        
        # 거리순 정렬
        nearby_locations.sort(key=lambda x: x["distance_meters"])
        
        return nearby_locations
    
    def get_service_radius_options(self) -> Dict[str, int]:
        """
        서비스 제공 거리 옵션들
        
        Returns:
            거리 옵션 딕셔너리 (분 단위)
        """
        return {
            "walking_5min": 5,      # 도보 5분 (같은 아파트 단지)
            "walking_10min": 10,    # 도보 10분 (같은 어린이집/놀이터)
            "walking_15min": 15,    # 도보 15분 (동네 기준)
            "walking_20min": 20,    # 도보 20분 (넓은 동네)
            "driving_5min": 5,      # 차량 5분
            "driving_10min": 10,    # 차량 10분
            "driving_15min": 15     # 차량 15분
        }

# 전역 인스턴스
location_service = LocationService()
