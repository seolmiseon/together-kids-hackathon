from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import os
import re
from rank_bm25 import BM25Okapi
import time


class VectorService:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.embeddings = OpenAIEmbeddings()
        self.persist_directory = persist_directory
        self.vector_store = Chroma(
            persist_directory=self.persist_directory, embedding_function=self.embeddings
        )
        # BM25 인덱스 및 문서 캐시
        self.bm25_index: Optional[BM25Okapi] = None
        self.bm25_documents: List[str] = []  # 원본 문서 텍스트
        self.bm25_doc_metadata: List[Dict[str, Any]] = []  # 문서 메타데이터
        self.bm25_last_update: Optional[float] = None
        self._initialize_bm25_index()

    async def add_schedule_info(
        self,
        user_id: str,
        schedule_text: str,
        intent: str = "schedule",
        urgency: str = "low",
    ):
        # 임베딩 단위 길이 체크 (예: 20~300자)
        if not (20 <= len(schedule_text) <= 300):
            logging.warning(f"임베딩 단위 길이 초과/미만: {len(schedule_text)}자")
            return
        try:
            metadata = {
                "user_id": user_id,
                "type": "schedule",
                "intent": intent,
                "urgency": urgency,
                "created_at": datetime.now().isoformat(),
            }
            self.vector_store.add_texts([schedule_text], metadatas=[metadata])
            self.vector_store.persist()
            # BM25 인덱스 업데이트
            self._update_bm25_index()
            logging.info(f"스케줄 저장됨: {user_id} - {schedule_text}")
        except Exception as e:
            logging.error(f"스케줄 저장 실패: {e}")

    async def search_similar_schedules(
        self, query_text: str, top_k: int = 3
    ) -> List[Dict[str, Any]]:
        results = self.vector_store.similarity_search_with_score(query_text, k=top_k)
        return [
            {"text": doc.page_content, "metadata": doc.metadata, "similarity": score}
            for doc, score in results
        ]

    async def search_similar_documents(
        self, query_text: str, top_k: int = 3, use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        통합 문서 검색 메서드
        use_hybrid=True일 경우 RRF Hybrid Search 사용, False일 경우 Vector Search만 사용
        """
        if use_hybrid:
            return await self.hybrid_search(query_text, top_k)
        else:
            return await self.search_similar_schedules(query_text, top_k)

    async def add_community_info(self, community_data: Dict[str, Any]):
        """커뮤니티 정보를 벡터 DB에 저장"""
        try:
            # 커뮤니티 정보를 검색 가능한 텍스트로 변환
            community_text = self._generate_community_vector_text(community_data)

            # 메타데이터 생성
            metadata = {
                "community_id": community_data.get("community_id"),
                "type": "community",
                "name": community_data.get("name"),
                "location": community_data.get("location"),
                "target_ages": ",".join(community_data.get("target_ages", [])),
                "focus_areas": ",".join(community_data.get("focus_areas", [])),
                "member_count": community_data.get("member_count", 0),
                "created_at": datetime.now().isoformat(),
            }

            # 벡터 DB에 저장
            self.vector_store.add_texts([community_text], metadatas=[metadata])
            self.vector_store.persist()
            # BM25 인덱스 업데이트
            self._update_bm25_index()
            logging.info(f"커뮤니티 저장됨: {community_data.get('name')}")

        except Exception as e:
            logging.error(f"커뮤니티 저장 실패: {e}")

    def _generate_community_vector_text(self, community_data: Dict[str, Any]) -> str:
        """커뮤니티 데이터를 벡터화용 텍스트로 변환"""
        text_parts = []

        # 기본 정보
        if community_data.get("name"):
            text_parts.append(f"커뮤니티명: {community_data['name']}")

        if community_data.get("location"):
            text_parts.append(f"지역: {community_data['location']}")

        if community_data.get("target_ages"):
            text_parts.append(f"대상연령: {', '.join(community_data['target_ages'])}")

        if community_data.get("focus_areas"):
            text_parts.append(f"주요관심사: {', '.join(community_data['focus_areas'])}")

        if community_data.get("activities"):
            text_parts.append(f"주요활동: {', '.join(community_data['activities'])}")

        if community_data.get("description"):
            text_parts.append(f"설명: {community_data['description']}")

        # 추가 정보
        if community_data.get("member_count"):
            text_parts.append(f"멤버수: {community_data['member_count']}명")

        if community_data.get("meeting_frequency"):
            text_parts.append(f"모임빈도: {community_data['meeting_frequency']}")

        if community_data.get("activity_style"):
            text_parts.append(
                f"활동스타일: {', '.join(community_data['activity_style'])}"
            )

        return " | ".join(text_parts)

    async def search_communities_by_profile(
        self, user_profile: Dict[str, Any], area: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """사용자 프로필 기반 커뮤니티 검색"""
        try:
            # 사용자 프로필을 검색 쿼리로 변환
            query_text = self._generate_search_query(user_profile, area)

            # 커뮤니티만 필터링하여 검색
            results = self.vector_store.similarity_search_with_score(
                query_text,
                k=top_k * 2,  # 더 많이 검색해서 필터링
                filter={"type": "community"},
            )

            # 지역 필터링 및 포맷팅
            filtered_results = []
            for doc, score in results:
                metadata = doc.metadata
                # 지역 매칭 확인
                if area.lower() in metadata.get("location", "").lower():
                    community_info = {
                        "community_id": metadata.get("community_id"),
                        "name": metadata.get("name"),
                        "location": metadata.get("location"),
                        "target_ages": (
                            metadata.get("target_ages", "").split(",")
                            if metadata.get("target_ages")
                            else []
                        ),
                        "focus_areas": (
                            metadata.get("focus_areas", "").split(",")
                            if metadata.get("focus_areas")
                            else []
                        ),
                        "member_count": metadata.get("member_count", 0),
                        "similarity_score": 1 - score,  # 점수 변환 (높을수록 유사)
                        "content": doc.page_content,
                    }
                    filtered_results.append(community_info)

                if len(filtered_results) >= top_k:
                    break

            return filtered_results

        except Exception as e:
            logging.error(f"커뮤니티 검색 실패: {e}")
            return []

    def _generate_search_query(self, user_profile: Dict[str, Any], area: str) -> str:
        """사용자 프로필을 검색 쿼리로 변환"""
        query_parts = []

        # 지역 정보
        query_parts.append(f"지역: {area}")

        # 육아 단계
        if user_profile.get("parenting_stage"):
            query_parts.append(f"육아단계: {user_profile['parenting_stage']}")

        # 교육 관심사
        if user_profile.get("education_interests"):
            query_parts.append(
                f"교육관심사: {', '.join(user_profile['education_interests'])}"
            )

        # 현재 니즈
        if user_profile.get("current_needs"):
            query_parts.append(
                f"필요한도움: {', '.join(user_profile['current_needs'])}"
            )

        # 활동 선호
        if user_profile.get("activity_preferences"):
            query_parts.append(
                f"선호활동: {', '.join(user_profile['activity_preferences'])}"
            )

        return " | ".join(query_parts)

    async def get_community_by_id(self, community_id: str) -> Dict[str, Any]:
        """커뮤니티 ID로 상세 정보 조회"""
        try:
            results = self.vector_store.similarity_search(
                community_id,
                k=1,
                filter={"community_id": community_id, "type": "community"},
            )

            if results:
                doc = results[0]
                metadata = doc.metadata
                return {
                    "community_id": metadata.get("community_id"),
                    "name": metadata.get("name"),
                    "location": metadata.get("location"),
                    "target_ages": (
                        metadata.get("target_ages", "").split(",")
                        if metadata.get("target_ages")
                        else []
                    ),
                    "focus_areas": (
                        metadata.get("focus_areas", "").split(",")
                        if metadata.get("focus_areas")
                        else []
                    ),
                    "member_count": metadata.get("member_count", 0),
                    "content": doc.page_content,
                }
            return {}

        except Exception as e:
            logging.error(f"커뮤니티 조회 실패: {e}")
            return {}

    # ========== RRF Hybrid Search 구현 ==========
    
    def _tokenize_korean(self, text: str) -> List[str]:
        """
        한국어 텍스트를 토큰화합니다.
        
        BM25는 키워드 기반 검색이므로 문서를 단어(토큰)로 나눠야 합니다.
        예시:
        - 입력: "아이가 밤에 잠을 안 자요"
        - 출력: ["아이", "밤", "잠", "자요", "안"] (토큰 리스트)
        
        토큰 = 단어 하나하나 (1개 문서 = 여러 개의 토큰)
        """
        # 공백으로 분리
        tokens = re.findall(r'\b\w+\b', text.lower())
        # 한글 문자 추출 (2글자 이상)
        korean_words = re.findall(r'[가-힣]{2,}', text)
        tokens.extend(korean_words)
        return list(set(tokens))  # 중복 제거
    
    def _initialize_bm25_index(self):
        """BM25 인덱스를 초기화합니다."""
        try:
            self._update_bm25_index()
            logging.info("BM25 인덱스 초기화 완료")
        except Exception as e:
            logging.warning(f"BM25 인덱스 초기화 실패 (문서가 없을 수 있음): {e}")
            self.bm25_index = None
    
    def _update_bm25_index(self):
        """
        ChromaDB에서 모든 문서를 가져와 BM25 인덱스를 구축/업데이트합니다.
        """
        try:
            # ChromaDB에서 모든 문서 가져오기
            # LangChain의 Chroma는 내부적으로 chromadb를 사용하므로 collection에 직접 접근
            collection = self.vector_store._collection
            
            # 모든 문서 조회 (최대 10000개)
            all_data = collection.get(limit=10000)
            
            if not all_data or not all_data.get('documents'):
                logging.warning("ChromaDB에 문서가 없습니다. BM25 인덱스를 건너뜁니다.")
                self.bm25_index = None
                self.bm25_documents = []
                self.bm25_doc_metadata = []
                return
            
            documents = all_data['documents']
            metadatas = all_data.get('metadatas', [{}] * len(documents))
            
            # 문서를 토큰화하여 BM25 인덱스 구축
            tokenized_docs = [self._tokenize_korean(doc) for doc in documents]
            
            if not tokenized_docs or not any(tokenized_docs):
                logging.warning("토큰화된 문서가 없습니다.")
                self.bm25_index = None
                return
            
            # BM25 인덱스 생성
            # BM25Okapi는 rank-bm25 라이브러리(공식 Python 패키지)에서 제공하는 클래스입니다
            # pip install rank-bm25로 설치 가능하며, 공식 문서: https://github.com/dorianbrown/rank_bm25
            self.bm25_index = BM25Okapi(tokenized_docs)
            self.bm25_documents = documents  # 원본 문서 텍스트 저장 (토큰화 전)
            self.bm25_doc_metadata = metadatas if metadatas else [{}] * len(documents)
            self.bm25_last_update = time.time()
            
            logging.info(f"BM25 인덱스 업데이트 완료: {len(documents)}개 문서")
            
        except Exception as e:
            logging.error(f"BM25 인덱스 업데이트 실패: {e}")
            self.bm25_index = None
    
    def _reciprocal_rank_fusion(
        self, 
        vector_results: List[Tuple[str, Dict[str, Any], float]], 
        bm25_results: List[Tuple[str, Dict[str, Any], float]], 
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        RRF (Reciprocal Rank Fusion) 알고리즘으로 두 검색 결과를 통합합니다.
        
        Args:
            vector_results: [(doc_text, metadata, score), ...] 형식의 벡터 검색 결과
            bm25_results: [(doc_text, metadata, score), ...] 형식의 BM25 검색 결과
            k: RRF 상수 (기본값 60)
        
        Returns:
            RRF 점수로 정렬된 통합 결과 리스트
        
        설명:
        "문서 텍스트를 직접 키로 사용" = Python 딕셔너리의 키로 문서 내용 자체를 사용
        예시:
        rrf_scores = {
            "아이가 밤에 잠을 안 자요": 0.5,  # 문서 텍스트 자체가 키
            "수면 교육 방법": 0.3
        }
        해시나 ID 대신 실제 문서 내용을 키로 사용하여 중복 문서를 자동으로 통합합니다.
        """
        # 문서 텍스트를 키로 하는 RRF 점수 딕셔너리
        # 예: rrf_scores["아이가 밤에 잠을 안 자요"] = 0.5
        rrf_scores = {}
        doc_data = {}  # 문서 데이터 저장
        
        # 벡터 검색 결과 처리
        for rank, (doc_text, metadata, score) in enumerate(vector_results, start=1):
            rrf_score = 1.0 / (k + rank)
            if doc_text not in rrf_scores:
                rrf_scores[doc_text] = 0.0
                doc_data[doc_text] = {
                    "text": doc_text,
                    "metadata": metadata,
                    "vector_score": score,
                    "bm25_score": 0.0
                }
            rrf_scores[doc_text] += rrf_score
            doc_data[doc_text]["vector_score"] = score
        
        # BM25 검색 결과 처리
        for rank, (doc_text, metadata, score) in enumerate(bm25_results, start=1):
            rrf_score = 1.0 / (k + rank)
            if doc_text not in rrf_scores:
                rrf_scores[doc_text] = 0.0
                doc_data[doc_text] = {
                    "text": doc_text,
                    "metadata": metadata,
                    "vector_score": 0.0,
                    "bm25_score": score
                }
            rrf_scores[doc_text] += rrf_score
            doc_data[doc_text]["bm25_score"] = score
        
        # RRF 점수로 정렬
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 결과 포맷팅
        results = []
        for doc_text, rrf_score in sorted_docs:
            doc_info = doc_data[doc_text]
            results.append({
                "text": doc_info["text"],
                "metadata": doc_info["metadata"],
                "similarity": rrf_score,  # RRF 점수를 similarity로 사용
                "vector_score": doc_info["vector_score"],
                "bm25_score": doc_info["bm25_score"],
                "rrf_score": rrf_score
            })
        
        return results
    
    async def hybrid_search(
        self, query_text: str, top_k: int = 5, vector_k: int = 10, bm25_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        RRF Hybrid Search: Semantic Search (Vector) + Keyword Search (BM25)를 RRF로 통합
        
        검색 방식:
        1. Semantic Search (Vector Search): 의미 유사도 기반 검색
           - OpenAI Embedding을 사용하여 텍스트를 벡터로 변환
           - 코사인 유사도로 의미가 비슷한 문서 검색
           - 예: "아이가 잠을 안 자요" → "수면 문제", "불면증" 등 의미상 유사한 문서 찾기
        
        2. Keyword Search (BM25): 정확한 키워드 매칭 검색
           - 문서를 토큰(단어)으로 분리하여 키워드 빈도 계산
           - 정확히 일치하는 키워드가 있는 문서 우선 검색
           - 예: "잠" 키워드가 포함된 문서를 직접 찾기
        
        3. RRF (Reciprocal Rank Fusion): 두 검색 결과 통합
           - 각 검색 결과의 순위를 점수로 변환하여 통합
           - 의미 검색과 키워드 검색의 장점을 결합
        
        Args:
            query_text: 검색 쿼리
            top_k: 최종 반환할 결과 수
            vector_k: Semantic Search에서 가져올 결과 수
            bm25_k: Keyword Search에서 가져올 결과 수
        
        Returns:
            RRF로 통합된 검색 결과 리스트
        
        왜 async로 만들었나요?
        - 기존 search_similar_documents()가 async였고, unified_chat_service에서 await로 호출합니다
        - 일관성을 위해 async로 구현했습니다 (실제로는 동기 작업이지만)
        
        왜 vector_service에 만들었나요?
        - 기존 RAG 검색 로직이 VectorService에 있습니다 (search_similar_documents)
        - RAGService는 LangChain의 RetrievalQA를 사용하는 간단한 래퍼일 뿐입니다
        - 실제 검색 로직은 VectorService가 담당하므로 여기에 추가하는 것이 맞습니다
        """
        start_time = time.time()
        
        try:
            # 1. Semantic Search (Vector Search) 수행
            # OpenAI Embedding을 사용하여 의미 유사도 기반 검색
            vector_results_raw = self.vector_store.similarity_search_with_score(
                query_text, k=vector_k
            )
            
            # Semantic Search 결과 포맷팅: (doc_text, metadata, score)
            vector_results = []
            for doc, score in vector_results_raw:
                doc_text = doc.page_content  # 문서 텍스트를 직접 사용
                vector_results.append((doc_text, doc.metadata, float(score)))
            
            # 2. Keyword Search (BM25) 수행
            # 키워드 빈도 기반 정확한 매칭 검색
            bm25_results = []
            if self.bm25_index is not None:
                try:
                    # 쿼리 토큰화
                    query_tokens = self._tokenize_korean(query_text)
                    
                    if query_tokens:
                        # BM25 점수 계산
                        bm25_scores = self.bm25_index.get_scores(query_tokens)
                        
                        # 상위 bm25_k개 결과 선택
                        top_indices = sorted(
                            range(len(bm25_scores)), 
                            key=lambda i: bm25_scores[i], 
                            reverse=True
                        )[:bm25_k]
                        
                        # BM25 결과 포맷팅
                        for idx in top_indices:
                            if idx < len(self.bm25_documents):
                                doc_text = self.bm25_documents[idx]
                                metadata = self.bm25_doc_metadata[idx] if idx < len(self.bm25_doc_metadata) else {}
                                score = float(bm25_scores[idx])
                                bm25_results.append((doc_text, metadata, score))
                except Exception as e:
                    logging.warning(f"BM25 검색 중 오류 발생: {e}")
                    # BM25 실패 시 벡터 검색만 사용
                    pass
            
            # BM25 인덱스가 없거나 업데이트가 필요한 경우
            if self.bm25_index is None:
                logging.info("BM25 인덱스가 없습니다. Semantic Search만 사용합니다.")
                # Semantic Search (Vector Search) 결과만 반환
                results = [
                    {
                        "text": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity": 1.0 - float(score),  # 거리를 유사도로 변환
                        "vector_score": float(score),
                        "bm25_score": 0.0,
                        "rrf_score": 0.0
                    }
                    for doc, score in vector_results_raw[:top_k]
                ]
            else:
                # 3. RRF로 Semantic Search와 Keyword Search 결과 통합
                rrf_results = self._reciprocal_rank_fusion(
                    vector_results, bm25_results, k=60
                )
                
                # 4. 최종 결과 반환 (이미 문서 텍스트가 포함되어 있음)
                results = rrf_results[:top_k]
            
            elapsed_time = time.time() - start_time
            logging.info(f"Hybrid Search 완료: {len(results)}개 결과, {elapsed_time:.3f}초 소요")
            
            return results
            
        except Exception as e:
            logging.error(f"Hybrid Search 실패: {e}")
            # 실패 시 기본 벡터 검색으로 폴백
            return await self.search_similar_schedules(query_text, top_k)
    
    async def refresh_bm25_index(self):
        """BM25 인덱스를 수동으로 새로고침합니다."""
        self._update_bm25_index()
