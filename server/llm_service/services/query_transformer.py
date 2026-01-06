"""
자연어 쿼리 전처리 서비스

네비게이션 API에 전달하기 전에 자연어 쿼리에서 핵심 키워드만 추출합니다.
예: "5살 아이와 가기 좋은 공원 추천해주세요" → "공원"
"""

import re
from typing import Optional
from openai import AsyncOpenAI
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class QueryTransformer:
    """자연어 쿼리를 검색 키워드로 변환하는 서비스"""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.openai_client = AsyncOpenAI(api_key=api_key)
        else:
            self.openai_client = None
            logger.warning("OpenAI API 키가 없습니다. 기본 키워드 추출만 사용합니다.")
    
    def extract_keyword_basic(self, query: str) -> str:
        """
        기본 키워드 추출 (정규식 기반)
        AI가 없을 때 사용하는 폴백 방법
        """
        # 장소 관련 키워드 추출
        place_keywords = [
            "공원", "놀이터", "키즈카페", "어린이", "수영장", "체육관", 
            "도서관", "박물관", "마트", "병원", "센터", "카페", "식당",
            "체험관", "놀이공원", "동물원", "수족관", "미술관"
        ]
        
        for keyword in place_keywords:
            if keyword in query:
                # 키워드 주변 텍스트 추출 (최대 10자)
                pattern = f"([가-힣\\w\\s]{{0,10}}{keyword}[가-힣\\w\\s]{{0,10}})"
                match = re.search(pattern, query)
                if match:
                    extracted = match.group(1).strip()
                    # 설명 제거 (예: "가기 좋은 공원" → "공원")
                    if len(extracted) > len(keyword) + 5:
                        return keyword
                    return extracted
        
        # 키워드를 찾지 못하면 원본 반환 (최대 20자)
        return query[:20].strip()
    
    async def transform_query(self, natural_language_query: str) -> str:
        """
        자연어 쿼리를 검색 키워드로 변환
        
        Args:
            natural_language_query: "5살 아이와 가기 좋은 공원 추천해주세요"
        
        Returns:
            "공원" (또는 "어린이 공원" 등 핵심 키워드만)
        """
        if not self.openai_client:
            return self.extract_keyword_basic(natural_language_query)
        
        try:
            prompt = f"""
다음 자연어 쿼리에서 네비게이션 검색에 사용할 핵심 키워드만 추출해주세요.

쿼리: {natural_language_query}

규칙:
1. 설명이나 문맥은 제거하고 장소명/키워드만 추출
2. 최대 3단어 이하로 간결하게
3. 검색 가능한 실제 장소명 우선
4. 예시:
   - "5살 아이와 가기 좋은 공원" → "공원"
   - "근처에 있는 키즈카페 추천" → "키즈카페"
   - "아이 수영 배우기 좋은 수영장" → "수영장"
   - "서울시청 근처 놀이터" → "놀이터"

핵심 키워드만 반환하세요 (설명 없이):
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 자연어 쿼리에서 검색 키워드를 추출하는 전문가입니다. 핵심 키워드만 간결하게 반환하세요."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 일관된 결과를 위해 낮은 temperature
                max_tokens=20
            )
            
            keyword = response.choices[0].message.content.strip()
            
            # 불필요한 설명 제거
            keyword = re.sub(r'[^가-힣\w\s]', '', keyword)  # 특수문자 제거
            keyword = keyword.strip()
            
            # 너무 길면 자르기
            if len(keyword) > 20:
                keyword = keyword[:20]
            
            logger.info(f"🔍 쿼리 변환: '{natural_language_query}' → '{keyword}'")
            return keyword if keyword else self.extract_keyword_basic(natural_language_query)
            
        except Exception as e:
            logger.error(f"쿼리 변환 실패: {e}")
            return self.extract_keyword_basic(natural_language_query)

