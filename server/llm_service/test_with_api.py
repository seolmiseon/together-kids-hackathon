"""
실제 API를 통한 Hybrid Search 테스트

서버를 실행한 후 실제 API 엔드포인트를 통해 테스트합니다.
이 방법은 실제 사용자 시나리오와 가장 유사합니다.

사용법:
    1. 서버 실행:
       cd server/llm_service
       python -m uvicorn main:app --reload --port 8002
    
    2. 새 터미널에서 테스트:
       python test_with_api.py
"""

import asyncio
import httpx
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8002"

async def test_unified_chat_api():
    """실제 API를 통한 Hybrid Search 테스트"""
    print("=" * 60)
    print("🚀 실제 API를 통한 Hybrid Search 테스트")
    print("=" * 60)
    
    # 테스트 쿼리들
    test_queries = [
        "아이가 밤에 잠을 안 자요",
        "수면 교육 방법 알려주세요",
        "육아 일정 관리하는 방법",
        "커뮤니티에서 정보 공유하고 싶어요"
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 테스트 {i}: '{query}'")
            print("-" * 60)
            
            try:
                # Unified Chat API 호출
                response = await client.post(
                    f"{BASE_URL}/chat/unified",
                    json={
                        "message": query,
                        "user_id": "test_user_api"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 응답 성공")
                    print(f"   응답: {data.get('response', '')[:100]}...")
                    print(f"   의도: {data.get('intent', 'N/A')}")
                    print(f"   긴급도: {data.get('urgency', 'N/A')}")
                else:
                    print(f"❌ 응답 실패: {response.status_code}")
                    print(f"   내용: {response.text}")
                    
            except httpx.ConnectError:
                print("❌ 서버에 연결할 수 없습니다.")
                print("\n💡 해결 방법:")
                print("   1. 서버가 실행 중인지 확인하세요:")
                print("      cd server/llm_service")
                print("      python -m uvicorn main:app --reload --port 8002")
                print("   2. 포트 8002가 사용 가능한지 확인하세요")
                return
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ API 테스트 완료!")
    print("=" * 60)

async def test_search_performance():
    """검색 성능 비교 테스트"""
    print("\n" + "=" * 60)
    print("📊 검색 성능 비교 테스트")
    print("=" * 60)
    
    import time
    from services.vector_service import VectorService
    
    vector_service = VectorService()
    query = "아이가 밤에 잠을 안 자요"
    
    # Vector Search만
    start = time.time()
    vector_results = await vector_service.search_similar_documents(
        query, top_k=5, use_hybrid=False
    )
    vector_time = time.time() - start
    
    # Hybrid Search
    start = time.time()
    hybrid_results = await vector_service.search_similar_documents(
        query, top_k=5, use_hybrid=True
    )
    hybrid_time = time.time() - start
    
    print(f"\n🔵 Vector Search만:")
    print(f"   시간: {vector_time:.3f}초")
    print(f"   결과: {len(vector_results)}개")
    
    print(f"\n🟢 Hybrid Search:")
    print(f"   시간: {hybrid_time:.3f}초")
    print(f"   결과: {len(hybrid_results)}개")
    print(f"   추가 시간: {hybrid_time - vector_time:.3f}초")
    
    # 결과 차이 확인
    vector_texts = {r['text'][:30] for r in vector_results}
    hybrid_texts = {r['text'][:30] for r in hybrid_results}
    
    if vector_texts != hybrid_texts:
        print(f"\n✅ Hybrid Search가 다른 결과를 반환했습니다!")
        print(f"   Vector만: {len(vector_texts - hybrid_texts)}개")
        print(f"   Hybrid만: {len(hybrid_texts - vector_texts)}개")
    else:
        print(f"\n⚠️  결과가 동일합니다 (데이터가 적거나 BM25 인덱스가 없을 수 있음)")

if __name__ == "__main__":
    print("\n선택하세요:")
    print("1. 실제 API 테스트 (서버 실행 필요)")
    print("2. 검색 성능 비교 테스트 (로컬)")
    
    choice = input("\n선택 (1 또는 2, 기본값: 2): ").strip() or "2"
    
    if choice == "1":
        asyncio.run(test_unified_chat_api())
    else:
        asyncio.run(test_search_performance())

