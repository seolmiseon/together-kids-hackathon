"""
RRF Hybrid Search 테스트 스크립트

로컬에서 Hybrid Search 기능을 테스트합니다.
서버를 실행하지 않고도 직접 테스트할 수 있습니다.

사용법:
    cd server/llm_service
    python test_hybrid_search.py
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (server/.env 또는 server/llm_service/.env)
env_paths = [
    Path(__file__).parent.parent.parent / ".env",  # server/.env
    Path(__file__).parent.parent / ".env",        # server/llm_service/.env
    Path(__file__).parent / ".env",                # 현재 디렉토리/.env
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ 환경 변수 로드: {env_path}")
        break
else:
    print("⚠️  .env 파일을 찾을 수 없습니다. 환경 변수를 확인하세요.")

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.vector_service import VectorService
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_hybrid_search():
    """Hybrid Search 기능 테스트 (기존 ChromaDB 데이터 사용)"""
    print("=" * 60)
    print("🚀 RRF Hybrid Search 테스트 시작 (실제 데이터)")
    print("=" * 60)
    
    # OpenAI API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("\n💡 해결 방법:")
        print("   1. server/.env 파일을 생성하세요")
        print("   2. 다음 내용을 추가하세요:")
        print("      OPENAI_API_KEY=sk-proj-xxxxx")
        print("\n   또는 환경 변수로 직접 설정:")
        print("   export OPENAI_API_KEY=sk-proj-xxxxx")
        return
    
    print(f"✅ OpenAI API 키 확인됨 (시작: {api_key[:10]}...)")
    
    # VectorService 초기화
    print("\n1️⃣ VectorService 초기화 중...")
    try:
        vector_service = VectorService()
        print("✅ VectorService 초기화 완료")
    except Exception as e:
        print(f"❌ VectorService 초기화 실패: {e}")
        print("\n💡 해결 방법:")
        print("   - OpenAI API 키가 올바른지 확인하세요")
        print("   - 인터넷 연결을 확인하세요")
        import traceback
        traceback.print_exc()
        return
    
    # ChromaDB 데이터 확인
    print("\n2️⃣ ChromaDB 데이터 확인 중...")
    try:
        collection = vector_service.vector_store._collection
        all_data = collection.get(limit=10000)
        doc_count = len(all_data.get('documents', []))
        
        if doc_count == 0:
            print("⚠️  ChromaDB에 문서가 없습니다.")
            print("\n💡 해결 방법:")
            print("   - 옵션 2를 선택하여 샘플 데이터를 추가하거나")
            print("   - 실제 애플리케이션을 통해 데이터를 추가하세요")
            return
        
        print(f"✅ ChromaDB에 {doc_count}개 문서가 있습니다")
        
        # 문서 샘플 보기
        if doc_count > 0:
            print("\n📄 문서 샘플 (최대 5개):")
            for i, doc in enumerate(all_data['documents'][:5], 1):
                preview = doc[:50] + "..." if len(doc) > 50 else doc
                print(f"   {i}. {preview}")
            
            if doc_count > 5:
                print(f"   ... 외 {doc_count - 5}개 문서")
    except Exception as e:
        print(f"⚠️  ChromaDB 데이터 확인 실패: {e}")
        print("   계속 진행합니다...")
    
    # 테스트 쿼리 입력 방식 선택
    print("\n3️⃣ 검색 테스트")
    print("-" * 60)
    print("\n테스트 쿼리 입력 방식:")
    print("1. 기본 테스트 쿼리 사용")
    print("2. 직접 입력 (대화형)")
    print("3. 파일에서 읽기")
    
    input_mode = input("\n선택 (1, 2, 또는 3, 기본값: 1): ").strip() or "1"
    
    if input_mode == "2":
        # 직접 입력 모드
        test_queries = []
        print("\n📝 테스트 쿼리를 입력하세요 (빈 줄 입력 시 종료):")
        while True:
            query = input("쿼리: ").strip()
            if not query:
                break
            test_queries.append(query)
        
        if not test_queries:
            print("⚠️  입력된 쿼리가 없습니다. 기본 쿼리를 사용합니다.")
            test_queries = ["아이가 밤에 잠을 안 자요"]
    elif input_mode == "3":
        # 파일에서 읽기
        file_path = input("쿼리 파일 경로 (한 줄에 하나씩): ").strip()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                test_queries = [line.strip() for line in f if line.strip()]
            print(f"✅ {len(test_queries)}개 쿼리를 파일에서 읽었습니다.")
        except Exception as e:
            print(f"❌ 파일 읽기 실패: {e}")
            print("기본 쿼리를 사용합니다.")
            test_queries = ["아이가 밤에 잠을 안 자요"]
    else:
        # 기본 테스트 쿼리
        test_queries = [
            "아이가 밤에 잠을 안 자요",
            "수면 문제",
            "육아 일정",
            "커뮤니티 찾기"
        ]
        print(f"\n✅ 기본 테스트 쿼리 {len(test_queries)}개를 사용합니다.")
    
    print("\n" + "-" * 60)
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 테스트 {i}: '{query}'")
        print("-" * 60)
        
        try:
            # Vector Search만 사용 (기존 방식)
            print("\n🔵 Vector Search만 사용:")
            vector_results = await vector_service.search_similar_documents(
                query, top_k=3, use_hybrid=False
            )
            print(f"   결과: {len(vector_results)}개")
            for j, result in enumerate(vector_results[:3], 1):
                text_preview = result['text'][:50] + "..." if len(result['text']) > 50 else result['text']
                print(f"   {j}. {text_preview}")
                print(f"      유사도: {result.get('similarity', 'N/A'):.4f}")
            
            # Hybrid Search 사용 (새로운 방식)
            print("\n🟢 Hybrid Search 사용 (Vector + BM25 + RRF):")
            hybrid_results = await vector_service.search_similar_documents(
                query, top_k=3, use_hybrid=True
            )
            print(f"   결과: {len(hybrid_results)}개")
            for j, result in enumerate(hybrid_results[:3], 1):
                text_preview = result['text'][:50] + "..." if len(result['text']) > 50 else result['text']
                print(f"   {j}. {text_preview}")
                print(f"      RRF 점수: {result.get('rrf_score', 'N/A'):.4f}")
                print(f"      Vector 점수: {result.get('vector_score', 'N/A'):.4f}")
                print(f"      BM25 점수: {result.get('bm25_score', 'N/A'):.4f}")
            
            # 결과 비교
            print("\n📊 결과 비교:")
            vector_texts = {r['text'][:30] for r in vector_results[:3]}
            hybrid_texts = {r['text'][:30] for r in hybrid_results[:3]}
            
            if vector_texts == hybrid_texts:
                print("   ⚠️  결과가 동일합니다 (BM25 인덱스가 없거나 문서가 적을 수 있음)")
            else:
                print("   ✅ Hybrid Search가 다른 결과를 반환했습니다!")
                print(f"   Vector만: {len(vector_texts - hybrid_texts)}개")
                print(f"   Hybrid만: {len(hybrid_texts - vector_texts)}개")
                
        except Exception as e:
            print(f"❌ 검색 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
    
    # BM25 인덱스 상태 확인
    print("\n3️⃣ BM25 인덱스 상태 확인")
    print("-" * 60)
    if vector_service.bm25_index is None:
        print("⚠️  BM25 인덱스가 없습니다.")
        print("   - ChromaDB에 문서가 없거나")
        print("   - 인덱스 초기화에 실패했을 수 있습니다")
        print("\n💡 해결 방법:")
        print("   - 먼저 문서를 추가해보세요:")
        print("     await vector_service.add_schedule_info('user1', '테스트 일정입니다')")
    else:
        print(f"✅ BM25 인덱스가 있습니다.")
        print(f"   - 문서 수: {len(vector_service.bm25_documents)}개")
        print(f"   - 마지막 업데이트: {vector_service.bm25_last_update}")
    
    print("\n" + "=" * 60)
    print("✅ 테스트 완료!")
    print("=" * 60)

async def test_with_sample_data():
    """샘플 데이터를 추가하고 테스트"""
    print("\n" + "=" * 60)
    print("📝 샘플 데이터 추가 및 테스트")
    print("=" * 60)
    
    vector_service = VectorService()
    
    # 샘플 문서 추가 (20자 이상인 문서들)
    # BM25가 제대로 작동하려면 최소 10-20개 문서가 권장됩니다
    sample_docs = [
        # 수면 관련 (5개)
        "아이가 밤에 잠을 안 자요. 어떻게 해야 할까요? 수면 교육이 필요할까요?",
        "밤에 아이가 깨서 울어요. 대처 방법은 무엇인가요? 수면 패턴을 개선하고 싶어요.",
        "수면 교육 방법에 대해 알려주세요. 아이가 잠들기 어려워하는데 도움이 필요합니다.",
        "아이 수면 패턴 개선하기 위한 구체적인 방법을 알고 싶어요. 수면 습관을 만들고 싶습니다.",
        "불면증 해결 방법을 찾고 있어요. 아이가 밤에 자주 깨서 걱정이 됩니다.",
        
        # 일정 관리 (5개)
        "육아 일정을 관리하는 방법을 알려주세요. 여러 아이의 일정을 효율적으로 관리하고 싶어요.",
        "어린이집 행사 일정을 잊지 않기 위한 방법이 필요해요. 알림 설정을 하고 싶습니다.",
        "의료 진료 일정을 관리하는 앱이나 방법을 추천해주세요. 예방접종 일정도 함께 관리하고 싶어요.",
        "육아 일정 공유 기능이 필요해요. 배우자와 함께 일정을 확인하고 싶습니다.",
        "아이의 일일 일정을 기록하고 관리하는 방법을 알고 싶어요. 수면 시간과 식사 시간을 추적하고 싶습니다.",
        
        # 커뮤니티 (5개)
        "커뮤니티에서 다른 부모님들과 정보를 공유하고 싶어요. 육아 경험을 나누고 싶습니다.",
        "근처 육아 커뮤니티를 찾고 있어요. 같은 지역의 부모님들과 만나고 싶습니다.",
        "공동구매 커뮤니티에 참여하고 싶어요. 기저귀나 분유를 함께 구매하고 싶습니다.",
        "육아 정보를 공유하는 온라인 커뮤니티를 추천해주세요. 신뢰할 수 있는 정보를 얻고 싶어요.",
        "아파트 단지 내 육아 모임을 만들고 싶어요. 이웃 부모님들과 교류하고 싶습니다.",
        
        # 건강/의료 (5개)
        "아이가 열이 나요. 언제 병원에 가야 할까요? 응급 상황인지 확인하고 싶어요.",
        "예방접종 일정을 확인하고 싶어요. 다음 접종이 언제인지 알려주세요.",
        "아이의 성장 발달이 정상인지 확인하고 싶어요. 월령별 발달 기준을 알고 싶습니다.",
        "소아과 추천을 받고 싶어요. 우리 지역에 좋은 소아과가 있을까요?",
        "아이 건강 검진 일정을 관리하고 싶어요. 정기 검진을 놓치지 않기 위한 방법이 필요합니다.",
        
        # 교육/놀이 (5개)
        "아이와 함께 할 수 있는 실내 놀이 활동을 추천해주세요. 비가 와서 집에 있어야 해요.",
        "유아 교육 프로그램을 찾고 있어요. 우리 아이 연령에 맞는 프로그램을 알고 싶습니다.",
        "독서 습관을 기르는 방법을 알려주세요. 아이가 책을 좋아하도록 만들고 싶어요.",
        "아이와 함께 갈 수 있는 교육 체험관을 추천해주세요. 주말에 가볼 만한 곳을 찾고 있어요.",
        "놀이터에서 안전하게 놀 수 있는 방법을 알려주세요. 아이가 다치지 않도록 주의사항을 알고 싶어요."
    ]
    
    print(f"\n📊 총 {len(sample_docs)}개 샘플 문서를 추가합니다.")
    print("   (BM25 효과를 확인하기 위해 다양한 주제의 문서를 포함했습니다)")
    
    print("\n1️⃣ 샘플 문서 추가 중...")
    for i, doc in enumerate(sample_docs, 1):
        try:
            await vector_service.add_schedule_info(
                user_id="test_user",
                schedule_text=doc,
                intent="general",
                urgency="low"
            )
            print(f"   ✅ 문서 {i} 추가: {doc[:30]}...")
        except Exception as e:
            print(f"   ❌ 문서 {i} 추가 실패: {e}")
    
    # 잠시 대기 (인덱스 업데이트 시간)
    print("\n2️⃣ BM25 인덱스 업데이트 대기 중...")
    await asyncio.sleep(1)
    
    # 테스트 쿼리 입력
    print("\n3️⃣ 검색 테스트")
    print("\n테스트 쿼리를 입력하세요:")
    print("1. 기본 쿼리 사용: '아이가 밤에 잠을 안 자요'")
    print("2. 직접 입력")
    
    query_choice = input("\n선택 (1 또는 2, 기본값: 1): ").strip() or "1"
    
    if query_choice == "2":
        query = input("\n테스트 쿼리 입력: ").strip()
        if not query:
            print("⚠️  입력이 없습니다. 기본 쿼리를 사용합니다.")
            query = "아이가 밤에 잠을 안 자요"
    else:
        query = "아이가 밤에 잠을 안 자요"
    
    print(f"\n   쿼리: '{query}'")
    
    print("\n   🔵 Vector Search만:")
    vector_results = await vector_service.search_similar_documents(
        query, top_k=3, use_hybrid=False
    )
    for i, result in enumerate(vector_results, 1):
        print(f"   {i}. {result['text'][:50]}...")
    
    print("\n   🟢 Hybrid Search:")
    hybrid_results = await vector_service.search_similar_documents(
        query, top_k=3, use_hybrid=True
    )
    for i, result in enumerate(hybrid_results, 1):
        print(f"   {i}. {result['text'][:50]}...")
        print(f"      RRF: {result.get('rrf_score', 0):.4f}, "
              f"Vector: {result.get('vector_score', 0):.4f}, "
              f"BM25: {result.get('bm25_score', 0):.4f}")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 RRF Hybrid Search 로컬 테스트")
    print("=" * 60)
    print("\n선택하세요:")
    print("1. 기존 데이터로 테스트 (ChromaDB에 데이터가 있는 경우)")
    print("2. 샘플 데이터 추가 후 테스트")
    
    choice = input("\n선택 (1 또는 2, 기본값: 1): ").strip() or "1"
    
    if choice == "2":
        asyncio.run(test_with_sample_data())
    else:
        asyncio.run(test_hybrid_search())

