"""
ChromaDB에 실제로 저장된 문서 수 확인 스크립트
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.vector_service import VectorService
import asyncio

async def check_chromadb():
    print("=" * 60)
    print("📊 ChromaDB 데이터 확인")
    print("=" * 60)
    
    vector_service = VectorService()
    
    # ChromaDB에서 직접 데이터 가져오기
    try:
        collection = vector_service.vector_store._collection
        all_data = collection.get(limit=10000)
        
        doc_count = len(all_data.get('documents', []))
        print(f"\n✅ ChromaDB에 저장된 문서 수: {doc_count}개")
        
        if doc_count > 0:
            print(f"\n📄 문서 목록 (최대 10개):")
            for i, doc in enumerate(all_data['documents'][:10], 1):
                preview = doc[:80] + "..." if len(doc) > 80 else doc
                print(f"   {i}. {preview}")
            
            if doc_count > 10:
                print(f"   ... 외 {doc_count - 10}개 문서")
            
            # 메타데이터 확인
            if all_data.get('metadatas'):
                print(f"\n📋 메타데이터 샘플:")
                for i, meta in enumerate(all_data['metadatas'][:3], 1):
                    print(f"   {i}. {meta}")
        else:
            print("\n⚠️  ChromaDB에 문서가 없습니다!")
            print("\n💡 샘플 데이터를 추가하려면:")
            print("   python test_hybrid_search.py")
            print("   → 옵션 2 선택 (샘플 데이터 추가 후 테스트)")
        
        # BM25 인덱스 상태
        print(f"\n🔍 BM25 인덱스 상태:")
        if vector_service.bm25_index is None:
            print("   ❌ BM25 인덱스가 없습니다")
        else:
            print(f"   ✅ BM25 인덱스 있음")
            print(f"   - 문서 수: {len(vector_service.bm25_documents)}개")
            print(f"   - 마지막 업데이트: {vector_service.bm25_last_update}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_chromadb())

