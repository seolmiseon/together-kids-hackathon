"""
Ground Truth 데이터 준비 스크립트

각 쿼리에 대해 검색 결과를 보여주고, 정답 문서를 선택할 수 있게 도와줍니다.

사용법:
    cd server/llm_service
    python prepare_ground_truth.py
"""
import asyncio
import os
import sys
import json
import hashlib
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
env_paths = [
    Path(__file__).parent.parent.parent / ".env",
    Path(__file__).parent.parent / ".env",
    Path(__file__).parent / ".env",
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.vector_service import VectorService
import logging

logging.basicConfig(level=logging.WARNING)  # 로그 최소화


async def show_search_results(vector_service, query: str, top_k: int = 10):
    """검색 결과를 보여주고 사용자가 정답을 선택할 수 있게 함"""
    print(f"\n{'='*60}")
    print(f"📝 쿼리: '{query}'")
    print(f"{'='*60}")
    
    # Hybrid Search 결과 가져오기
    results = await vector_service.search_similar_documents(
        query, top_k=top_k, use_hybrid=True
    )
    
    if not results:
        print("⚠️  검색 결과가 없습니다.")
        return []
    
    print(f"\n🔍 검색 결과 (상위 {len(results)}개):")
    print("-" * 60)
    
    # 결과 표시
    selected_indices = []
    for i, result in enumerate(results, 1):
        text = result['text']
        preview = text[:80] + "..." if len(text) > 80 else text
        
        # 문서 ID 추출 (metadata에서 가져오거나 텍스트 해시 사용 - 일관된 해시)
        doc_id = result.get('metadata', {}).get('id', f"doc_{int(hashlib.md5(text.encode()).hexdigest(), 16) % 1000000}")
        
        print(f"\n[{i}] ID: {doc_id}")
        print(f"    {preview}")
        if 'rrf_score' in result:
            print(f"    RRF 점수: {result.get('rrf_score', 0):.4f}")
    
    # 정답 선택
    print(f"\n{'='*60}")
    print("✅ 정답 문서를 선택하세요 (여러 개 선택 가능)")
    print("   예: 1,3,5 또는 1-3 또는 'all' (모두 선택)")
    print("   빈 줄 입력 시 이 쿼리 건너뛰기")
    
    user_input = input("\n선택: ").strip()
    
    if not user_input:
        print("⏭️  이 쿼리를 건너뜁니다.")
        return []
    
    if user_input.lower() == 'all':
        selected_indices = list(range(len(results)))
    else:
        # 입력 파싱 (1,3,5 또는 1-3 형식)
        try:
            parts = user_input.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # 범위 (1-3)
                    start, end = map(int, part.split('-'))
                    selected_indices.extend(range(start-1, end))
                else:
                    # 단일 번호
                    selected_indices.append(int(part) - 1)
        except ValueError:
            print("❌ 잘못된 입력입니다. 건너뜁니다.")
            return []
    
    # 선택된 문서 ID 반환
    selected_doc_ids = []
    for idx in selected_indices:
        if 0 <= idx < len(results):
            text = results[idx]['text']
            text = results[idx]['text']
            doc_id = results[idx].get('metadata', {}).get('id', f"doc_{int(hashlib.md5(text.encode()).hexdigest(), 16) % 1000000}")
            selected_doc_ids.append(doc_id)
    
    print(f"✅ {len(selected_doc_ids)}개 문서를 정답으로 선택했습니다.")
    return selected_doc_ids


async def prepare_ground_truth():
    """Ground Truth 데이터 준비"""
    print("=" * 60)
    print("📊 Ground Truth 데이터 준비")
    print("=" * 60)
    print("\n이 스크립트는 각 쿼리에 대해 검색 결과를 보여주고,")
    print("정답 문서를 선택할 수 있게 도와줍니다.")
    print("\n💡 팁:")
    print("   - 쿼리와 관련성이 높은 문서를 정답으로 선택하세요")
    print("   - 여러 개 선택 가능합니다")
    print("   - 확실하지 않으면 건너뛰고 나중에 수정할 수 있습니다")
    
    # VectorService 초기화
    print("\n1️⃣ VectorService 초기화 중...")
    try:
        vector_service = VectorService()
        print("✅ 초기화 완료")
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return
    
    # 테스트 쿼리 목록
    test_queries = [
        "아이가 밤에 잠을 안 자요",
        "수면 문제 해결 방법",
        "육아 일정 관리",
        "커뮤니티 찾기",
        "예방접종 일정",
    ]
    
    print(f"\n2️⃣ {len(test_queries)}개 쿼리에 대해 정답을 선택합니다.")
    print("   (각 쿼리마다 검색 결과를 보여드립니다)")
    
    ground_truth = {}
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(test_queries)}]")
        
        selected_ids = await show_search_results(vector_service, query, top_k=10)
        
        if selected_ids:
            ground_truth[query] = selected_ids
            print(f"✅ '{query}' → {len(selected_ids)}개 정답 문서")
        else:
            print(f"⏭️  '{query}' 건너뜀")
    
    # 결과 저장
    if ground_truth:
        # 현재 스크립트가 있는 디렉토리에 저장
        script_dir = Path(__file__).parent
        output_file = script_dir / "ground_truth.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ground_truth, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"✅ Ground Truth 데이터 저장 완료!")
        print(f"   파일: {output_file}")
        print(f"   총 {len(ground_truth)}개 쿼리의 정답 데이터")
        print(f"\n💡 이 파일을 measure_search_accuracy.py에서 사용할 수 있습니다.")
        
        # 미리보기
        print(f"\n📋 저장된 데이터 미리보기:")
        for query, doc_ids in list(ground_truth.items())[:3]:
            print(f"   '{query}': {len(doc_ids)}개 정답")
    else:
        print("\n⚠️  정답 데이터가 없습니다.")
    
    print("\n" + "=" * 60)
    print("✅ 완료!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(prepare_ground_truth())

