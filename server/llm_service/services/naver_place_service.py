import os
import httpx
from typing import List, Dict, Any
import asyncio
from urllib.parse import quote
from urllib.parse import quote

class NaverPlaceService:
    def __init__(self):
        self.client_id = os.getenv("NAVER_CLIENT_ID")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET")
        
        if not self.client_id or not self.client_secret:
            print("⚠️ 네이버 API 키가 설정되지 않았습니다.")
    
    async def search_nearby_places(self, query: str, lat: float, lng: float, radius: int = 2000) -> List[Dict[str, Any]]:
        """네이버 지역검색 API로 주변 장소 검색"""
        if not self.client_id or not self.client_secret:
            return []
        
        try:
            headers = {
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.client_secret
            }
            
            # 기본 검색 (리뷰 많은 순)
            params = {
                "query": query,
                "display": 5,  # 최대 5개 결과
                "start": 1,
                "sort": "comment"  # 리뷰 많은 순 정렬
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://openapi.naver.com/v1/search/local.json",
                    headers=headers,
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    places = []
                    
                    for item in data.get("items", []):
                        place = {
                            "name": item.get("title", "").replace("<b>", "").replace("</b>", ""),
                            "address": item.get("address", ""),
                            "description": item.get("description", ""),
                            "telephone": item.get("telephone", ""),
                            "category": item.get("category", ""),
                            "roadAddress": item.get("roadAddress", "")
                        }
                        places.append(place)
                    
                    return places
                else:
                    print(f"네이버 API 오류: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"네이버 장소 검색 오류: {e}")
            return []
    
    async def search_water_places(self, lat: float, lng: float) -> List[Dict[str, Any]]:
        """물놀이 관련 장소 검색"""
        water_keywords = ["물놀이터", "수영장", "워터파크", "물놀이", "실내수영장"]
        all_places = []
        
        for keyword in water_keywords:
            places = await self.search_nearby_places(keyword, lat, lng)
            all_places.extend(places)
        
        # 중복 제거 (이름 기준)
        unique_places = []
        seen_names = set()
        
        for place in all_places:
            if place["name"] not in seen_names:
                unique_places.append(place)
                seen_names.add(place["name"])
        
        return unique_places[:5]  # 최대 5개만 반환
