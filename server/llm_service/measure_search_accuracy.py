"""
RRF Hybrid Search 정확도 측정 스크립트

사용법:
    cd server/llm_service
    python measure_search_accuracy.py

측정 방법:
1. 자동 측정 (결과 순위 비교)
   - Vector Search와 Hybrid Search 결과의 순위 차이 측정
   - 결과가 얼마나 다른지, 순위가 개선되었는지 측정

2. 수동 평가 (Ground Truth 필요)
   - 각 쿼리에 대한 정답 문서 ID 리스트 준비
   - Precision@K, Recall@K 계산

3. 실제 사용자 피드백 기반
   - 사용자가 "도움됨" 버튼 클릭 비율
   - 응답 만족도 점수
"""

import asyncio
import os
import sys
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Set, Tuple
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SearchAccuracyMeasurer:
    """검색 정확도 측정 클래스"""
    
    def __init__(self, vector_service: VectorService):
        self.vector_service = vector_service
    
    def calculate_precision_at_k(self, retrieved: List[str], relevant: Set[str], k: int) -> float:
        """Precision@K 계산
        
        Args:
            retrieved: 검색된 문서 ID 리스트 (순위 순)
            relevant: 정답 문서 ID 집합
            k: 상위 K개만 고려
        
        Returns:
            Precision@K 값 (0.0 ~ 1.0)
        """
        if k == 0:
            return 0.0
        
        top_k = retrieved[:k]
        relevant_retrieved = sum(1 for doc_id in top_k if doc_id in relevant)
        return relevant_retrieved / k
    
    def calculate_recall_at_k(self, retrieved: List[str], relevant: Set[str], k: int) -> float:
        """Recall@K 계산
        
        Args:
            retrieved: 검색된 문서 ID 리스트 (순위 순)
            relevant: 정답 문서 ID 집합
            k: 상위 K개만 고려
        
        Returns:
            Recall@K 값 (0.0 ~ 1.0)
        """
        if len(relevant) == 0:
            return 0.0
        
        top_k = retrieved[:k]
        relevant_retrieved = sum(1 for doc_id in top_k if doc_id in relevant)
        return relevant_retrieved / len(relevant)
    
    def calculate_mrr(self, retrieved: List[str], relevant: Set[str]) -> float:
        """Mean Reciprocal Rank (MRR) 계산
        
        Args:
            retrieved: 검색된 문서 ID 리스트 (순위 순)
            relevant: 정답 문서 ID 집합
        
        Returns:
            MRR 값 (0.0 ~ 1.0)
        """
        for rank, doc_id in enumerate(retrieved, start=1):
            if doc_id in relevant:
                return 1.0 / rank
        return 0.0
    
    def calculate_rank_improvement(
        self, 
        vector_results: List[Dict], 
        hybrid_results: List[Dict]
    ) -> Dict[str, float]:
        """결과 순위 개선도 측정
        
        같은 문서가 Vector Search와 Hybrid Search에서 
        얼마나 다른 순위에 있는지 측정
        
        Returns:
            {
                'avg_rank_improvement': 평균 순위 개선도,
                'improved_count': 순위가 개선된 문서 수,
                'worsened_count': 순위가 악화된 문서 수,
                'same_count': 순위가 동일한 문서 수
            }
        """
        # 문서 텍스트를 키로 사용 (ID가 없을 수 있으므로)
        vector_ranks = {r['text']: rank for rank, r in enumerate(vector_results, start=1)}
        hybrid_ranks = {r['text']: rank for rank, r in enumerate(hybrid_results, start=1)}
        
        # 공통 문서 찾기
        common_docs = set(vector_ranks.keys()) & set(hybrid_ranks.keys())
        
        if not common_docs:
            return {
                'avg_rank_improvement': 0.0,
                'improved_count': 0,
                'worsened_count': 0,
                'same_count': 0,
                'total_common': 0
            }
        
        rank_diffs = []
        improved = 0
        worsened = 0
        same = 0
        
        for doc_text in common_docs:
            vector_rank = vector_ranks[doc_text]
            hybrid_rank = hybrid_ranks[doc_text]
            diff = vector_rank - hybrid_rank  # 양수면 개선, 음수면 악화
            
            rank_diffs.append(diff)
            if diff > 0:
                improved += 1
            elif diff < 0:
                worsened += 1
            else:
                same += 1
        
        avg_improvement = sum(rank_diffs) / len(rank_diffs) if rank_diffs else 0.0
        
        return {
            'avg_rank_improvement': avg_improvement,
            'improved_count': improved,
            'worsened_count': worsened,
            'same_count': same,
            'total_common': len(common_docs)
        }
    
    def calculate_result_diversity(
        self, 
        vector_results: List[Dict], 
        hybrid_results: List[Dict]
    ) -> Dict[str, float]:
        """결과 다양성 측정
        
        Vector Search와 Hybrid Search가 얼마나 다른 결과를 반환하는지 측정
        
        Returns:
            {
                'overlap_ratio': 겹치는 결과 비율,
                'unique_vector': Vector만 있는 결과 수,
                'unique_hybrid': Hybrid만 있는 결과 수
            }
        """
        vector_texts = {r['text'][:100] for r in vector_results}  # 처음 100자로 비교
        hybrid_texts = {r['text'][:100] for r in hybrid_results}
        
        total_unique = len(vector_texts | hybrid_texts)
        overlap = len(vector_texts & hybrid_texts)
        
        if total_unique == 0:
            return {
                'overlap_ratio': 0.0,
                'unique_vector': 0,
                'unique_hybrid': 0
            }
        
        return {
            'overlap_ratio': overlap / total_unique,
            'unique_vector': len(vector_texts - hybrid_texts),
            'unique_hybrid': len(hybrid_texts - vector_texts)
        }
    
    async def measure_single_query(
        self, 
        query: str, 
        top_k: int = 5,
        ground_truth: Set[str] = None
    ) -> Dict:
        """단일 쿼리에 대한 정확도 측정"""
        
        # Vector Search
        start_time = time.time()
        vector_results = await self.vector_service.search_similar_documents(
            query, top_k=top_k, use_hybrid=False
        )
        vector_time = time.time() - start_time
        
        # Hybrid Search
        start_time = time.time()
        hybrid_results = await self.vector_service.search_similar_documents(
            query, top_k=top_k, use_hybrid=True
        )
        hybrid_time = time.time() - start_time
        
        # 기본 측정값
        measurements = {
            'query': query,
            'vector_time': vector_time,
            'hybrid_time': hybrid_time,
            'time_overhead': hybrid_time - vector_time,
            'vector_count': len(vector_results),
            'hybrid_count': len(hybrid_results),
        }
        
        # 순위 개선도 측정
        rank_improvement = self.calculate_rank_improvement(vector_results, hybrid_results)
        # 키 이름을 그대로 사용 (rank_ 접두사 제거)
        measurements.update(rank_improvement)
        
        # 결과 다양성 측정
        diversity = self.calculate_result_diversity(vector_results, hybrid_results)
        # 키 이름을 그대로 사용 (diversity_ 접두사 제거)
        measurements.update(diversity)
        
        # 디버깅: 실제 결과 비교 정보 추가
        measurements['vector_result_texts'] = [r['text'][:50] for r in vector_results[:3]]
        measurements['hybrid_result_texts'] = [r['text'][:50] for r in hybrid_results[:3]]
        
        # Ground Truth가 있으면 Precision/Recall 계산
        if ground_truth:
            # 문서 ID 추출 (metadata에서 가져오거나 텍스트 해시 사용 - 일관된 해시)
            def get_doc_id(result):
                text = result['text']
                return result.get('metadata', {}).get('id', f"doc_{int(hashlib.md5(text.encode()).hexdigest(), 16) % 1000000}")
            
            vector_ids = [get_doc_id(r) for r in vector_results]
            hybrid_ids = [get_doc_id(r) for r in hybrid_results]
            
            # Precision@K, Recall@K 계산
            for k in [1, 3, 5]:
                if k <= top_k:
                    measurements[f'vector_precision@{k}'] = self.calculate_precision_at_k(
                        vector_ids, ground_truth, k
                    )
                    measurements[f'hybrid_precision@{k}'] = self.calculate_precision_at_k(
                        hybrid_ids, ground_truth, k
                    )
                    measurements[f'vector_recall@{k}'] = self.calculate_recall_at_k(
                        vector_ids, ground_truth, k
                    )
                    measurements[f'hybrid_recall@{k}'] = self.calculate_recall_at_k(
                        hybrid_ids, ground_truth, k
                    )
            
            # MRR 계산
            measurements['vector_mrr'] = self.calculate_mrr(vector_ids, ground_truth)
            measurements['hybrid_mrr'] = self.calculate_mrr(hybrid_ids, ground_truth)
        
        return measurements
    
    async def measure_batch(
        self, 
        test_queries: List[Tuple[str, Set[str]]],
        top_k: int = 5
    ) -> Dict:
        """여러 쿼리에 대한 배치 측정
        
        Args:
            test_queries: [(query, ground_truth_set), ...] 리스트
            top_k: 상위 K개 결과만 고려
        
        Returns:
            전체 통계 결과
        """
        all_measurements = []
        
        print(f"\n📊 {len(test_queries)}개 쿼리 측정 시작...")
        print("=" * 60)
        
        for i, (query, ground_truth) in enumerate(test_queries, 1):
            print(f"\n[{i}/{len(test_queries)}] '{query}'")
            try:
                measurement = await self.measure_single_query(query, top_k, ground_truth)
                all_measurements.append(measurement)
                
                # 간단한 진행 상황 출력
                rank_improvement = measurement.get('avg_rank_improvement', 0)
                total_common = measurement.get('total_common', 0)
                improved = measurement.get('improved_count', 0)
                worsened = measurement.get('worsened_count', 0)
                same = measurement.get('same_count', 0)
                
                print(f"   순위 개선도: {rank_improvement:+.2f} (공통 문서: {total_common}개)")
                if total_common > 0:
                    print(f"   개선: {improved}개, 악화: {worsened}개, 동일: {same}개")
                else:
                    print(f"   ⚠️  공통 문서가 없습니다 (결과가 완전히 다름)")
                
                print(f"   시간: 🟢 Hybrid {measurement['hybrid_time']:.3f}s (리팩토링 후), "
                      f"🔵 Vector {measurement['vector_time']:.3f}s (리팩토링 전)")
                
                # 데이터 부족 경고
                if measurement['vector_count'] < top_k:
                    print(f"   ⚠️  데이터 부족: {measurement['vector_count']}개 문서만 존재 (요청: {top_k}개)")
            except Exception as e:
                logger.error(f"쿼리 '{query}' 측정 실패: {e}")
                continue
        
        # 통계 계산
        if not all_measurements:
            return {'error': '측정 결과가 없습니다.'}
        
        stats = self._calculate_statistics(all_measurements)
        return stats
    
    def _calculate_statistics(self, measurements: List[Dict]) -> Dict:
        """측정 결과 통계 계산"""
        stats = {
            'total_queries': len(measurements),
            'avg_vector_time': sum(m['vector_time'] for m in measurements) / len(measurements),
            'avg_hybrid_time': sum(m['hybrid_time'] for m in measurements) / len(measurements),
            'avg_time_overhead': sum(m['time_overhead'] for m in measurements) / len(measurements),
        }
        
        # 순위 개선도 통계
        rank_improvements = [m.get('avg_rank_improvement', 0) for m in measurements]
        if rank_improvements:
            stats['avg_rank_improvement'] = sum(rank_improvements) / len(rank_improvements)
            stats['max_rank_improvement'] = max(rank_improvements)
            stats['min_rank_improvement'] = min(rank_improvements)
        
        # 결과 다양성 통계
        diversity_ratios = [m.get('overlap_ratio', 0) for m in measurements]
        if diversity_ratios:
            stats['avg_diversity_overlap'] = sum(diversity_ratios) / len(diversity_ratios)
        
        # 데이터 부족 여부 확인 (실제 ChromaDB 문서 수 확인)
        try:
            collection = self.vector_service.vector_store._collection
            all_data = collection.get(limit=10000)
            actual_doc_count = len(all_data.get('documents', []))
            stats['total_documents'] = actual_doc_count
            stats['data_sufficient'] = actual_doc_count >= 10  # 최소 10개 문서 권장
        except Exception:
            # 폴백: 측정값에서 최대값 사용
            total_docs = max([m.get('vector_count', 0) for m in measurements] + [0])
            stats['total_documents'] = total_docs
            stats['data_sufficient'] = total_docs >= 10
        
        # Ground Truth 기반 지표 (있는 경우)
        precision_keys = [k for k in measurements[0].keys() if 'precision@' in k]
        if precision_keys:
            for key in precision_keys:
                values = [m[key] for m in measurements if key in m]
                if values:
                    stats[f'avg_{key}'] = sum(values) / len(values)
        
        recall_keys = [k for k in measurements[0].keys() if 'recall@' in k]
        if recall_keys:
            for key in recall_keys:
                values = [m[key] for m in measurements if key in m]
                if values:
                    stats[f'avg_{key}'] = sum(values) / len(values)
        
        mrr_keys = [k for k in measurements[0].keys() if 'mrr' in k]
        if mrr_keys:
            for key in mrr_keys:
                values = [m[key] for m in measurements if key in m]
                if values:
                    stats[f'avg_{key}'] = sum(values) / len(values)
        
        return stats


async def main():
    """메인 함수"""
    print("=" * 60)
    print("📊 Hybrid Search 정확도 측정 (리팩토링 후)")
    print("   리팩토링 전(Vector)과 비교하여 성능 측정")
    print("=" * 60)
    
    # VectorService 초기화
    print("\n1️⃣ VectorService 초기화 중...")
    try:
        vector_service = VectorService()
        print("✅ 초기화 완료")
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return
    
    measurer = SearchAccuracyMeasurer(vector_service)
    
    # 측정 모드 선택
    print("\n2️⃣ 측정 모드 선택:")
    print("1. 자동 측정 (순위 개선도 + 결과 다양성)")
    print("2. Ground Truth 기반 측정 (Precision/Recall/MRR)")
    print("3. 사용자 정의 테스트 쿼리")
    
    mode = input("\n선택 (1, 2, 또는 3, 기본값: 1): ").strip() or "1"
    
    if mode == "1":
        # 자동 측정 모드
        test_queries = [
            ("아이가 밤에 잠을 안 자요", set()),
            ("수면 문제 해결 방법", set()),
            ("육아 일정 관리", set()),
            ("커뮤니티 찾기", set()),
            ("예방접종 일정", set()),
        ]
        
        print(f"\n📝 {len(test_queries)}개 기본 테스트 쿼리 사용")
        stats = await measurer.measure_batch(
            [(q, gt) for q, gt in test_queries],
            top_k=5
        )
        
    elif mode == "2":
        # Ground Truth 기반 측정
        print("\n2️⃣ Ground Truth 데이터 로드 중...")
        
        # ground_truth.json 파일 읽기
        script_dir = Path(__file__).parent
        ground_truth_file = script_dir / "ground_truth.json"
        
        if not ground_truth_file.exists():
            print(f"❌ Ground Truth 파일을 찾을 수 없습니다: {ground_truth_file}")
            print(f"\n💡 먼저 prepare_ground_truth.py를 실행하여 정답 데이터를 준비하세요:")
            print(f"   python prepare_ground_truth.py")
            return
        
        try:
            with open(ground_truth_file, 'r', encoding='utf-8') as f:
                ground_truth_data = json.load(f)
            
            print(f"✅ Ground Truth 데이터 로드 완료: {len(ground_truth_data)}개 쿼리")
            
            # Ground Truth 데이터를 쿼리 리스트로 변환
            test_queries = [
                (query, set(doc_ids)) 
                for query, doc_ids in ground_truth_data.items()
            ]
            
            print(f"\n📝 {len(test_queries)}개 쿼리로 Precision/Recall/MRR 측정 시작...")
            stats = await measurer.measure_batch(test_queries, top_k=5)
            
        except json.JSONDecodeError as e:
            print(f"❌ Ground Truth 파일 파싱 실패: {e}")
            return
        except Exception as e:
            print(f"❌ Ground Truth 파일 읽기 실패: {e}")
            return
        
    else:
        # 사용자 정의 쿼리
        print("\n📝 테스트 쿼리를 입력하세요 (빈 줄 입력 시 종료):")
        queries = []
        while True:
            query = input("쿼리: ").strip()
            if not query:
                break
            queries.append((query, set()))
        
        if not queries:
            print("⚠️  입력된 쿼리가 없습니다.")
            return
        
        stats = await measurer.measure_batch(queries, top_k=5)
    
    # 결과 출력
    print("\n" + "=" * 60)
    print("📊 측정 결과 요약 (리팩토링 후: Hybrid Search 기준)")
    print("=" * 60)
    
    print(f"\n✅ 총 쿼리 수: {stats.get('total_queries', 0)}개")
    
    # 데이터 부족 경고
    total_docs = stats.get('total_documents', 0)
    if total_docs < 10:
        print(f"\n⚠️  데이터 부족 경고:")
        print(f"   현재 문서 수: {total_docs}개")
        print(f"   권장 문서 수: 최소 10개 이상 (현재는 {total_docs}개만 있어서")
        print(f"   리팩토링 전(Vector)과 리팩토링 후(Hybrid)가 동일한 결과를 반환할 수 있습니다)")
        print(f"\n💡 해결 방법:")
        print(f"   - test_hybrid_search.py의 옵션 2를 선택하여 샘플 데이터 추가")
        print(f"   - 또는 실제 애플리케이션을 통해 더 많은 데이터 추가")
    
    if 'avg_vector_time' in stats:
        print(f"\n⏱️  평균 검색 시간:")
        print(f"   🟢 Hybrid Search (리팩토링 후, 현재 사용): {stats['avg_hybrid_time']:.3f}초")
        print(f"   🔵 Vector Search (리팩토링 전, 비교용): {stats['avg_vector_time']:.3f}초")
        overhead = stats['avg_time_overhead']
        if overhead < 0:
            print(f"   ⚡ Hybrid가 {abs(overhead):.3f}초 더 빠름!")
        else:
            print(f"   ⚠️  Hybrid가 {overhead:.3f}초 더 느림 (데이터가 적어서일 수 있음)")
    
    if 'avg_rank_improvement' in stats:
        print(f"\n📈 순위 개선도 (리팩토링 전 대비):")
        print(f"   평균: {stats['avg_rank_improvement']:+.2f}")
        print(f"   최대: {stats.get('max_rank_improvement', 0):+.2f}")
        print(f"   최소: {stats.get('min_rank_improvement', 0):+.2f}")
        print(f"   (양수 = Hybrid가 개선, 음수 = Hybrid가 악화, 0 = 동일)")
    
    if 'avg_diversity_overlap' in stats:
        print(f"\n🔄 결과 다양성:")
        print(f"   겹치는 결과 비율: {stats['avg_diversity_overlap']:.1%}")
    
    # Precision/Recall 결과 출력 (Hybrid Search 메인)
    precision_keys = [k for k in stats.keys() if 'precision@' in k]
    if precision_keys:
        print(f"\n🎯 Precision@K:")
        # Hybrid Search 먼저 출력
        hybrid_precision = [k for k in sorted(precision_keys) if 'hybrid' in k]
        vector_precision = [k for k in sorted(precision_keys) if 'vector' in k]
        for key in hybrid_precision:
            k = key.split('@')[1]
            print(f"   🟢 Hybrid Search (리팩토링 후): {stats[key]:.1%}")
        for key in vector_precision:
            k = key.split('@')[1]
            print(f"   🔵 Vector Search (리팩토링 전, 비교용): {stats[key]:.1%}")
    
    recall_keys = [k for k in stats.keys() if 'recall@' in k]
    if recall_keys:
        print(f"\n📊 Recall@K:")
        # Hybrid Search 먼저 출력
        hybrid_recall = [k for k in sorted(recall_keys) if 'hybrid' in k]
        vector_recall = [k for k in sorted(recall_keys) if 'vector' in k]
        for key in hybrid_recall:
            k = key.split('@')[1]
            print(f"   🟢 Hybrid Search (리팩토링 후): {stats[key]:.1%}")
        for key in vector_recall:
            k = key.split('@')[1]
            print(f"   🔵 Vector Search (리팩토링 전, 비교용): {stats[key]:.1%}")
    
    mrr_keys = [k for k in stats.keys() if 'mrr' in k]
    if mrr_keys:
        print(f"\n🏆 MRR (Mean Reciprocal Rank):")
        # Hybrid Search 먼저 출력
        hybrid_mrr = [k for k in sorted(mrr_keys) if 'hybrid' in k]
        vector_mrr = [k for k in sorted(mrr_keys) if 'vector' in k]
        for key in hybrid_mrr:
            print(f"   🟢 Hybrid Search (리팩토링 후): {stats[key]:.3f}")
        for key in vector_mrr:
            print(f"   🔵 Vector Search (리팩토링 전, 비교용): {stats[key]:.3f}")
    
    # 개선율 계산
    if 'avg_hybrid_precision@5' in stats and 'avg_vector_precision@5' in stats:
        improvement = (
            (stats['avg_hybrid_precision@5'] - stats['avg_vector_precision@5']) 
            / stats['avg_vector_precision@5'] * 100
            if stats['avg_vector_precision@5'] > 0 else 0
        )
        print(f"\n🚀 리팩토링 후 개선율 (Precision@5): {improvement:+.1f}%")
        print(f"   (리팩토링 전 Vector Search 대비)")
    
    print("\n" + "=" * 60)
    print("✅ 측정 완료!")
    print("=" * 60)
    
    # 결과를 파일로 저장할지 물어보기
    save = input("\n결과를 파일로 저장하시겠습니까? (y/n, 기본값: n): ").strip().lower()
    if save == 'y':
        from datetime import datetime
        
        filename = f"search_accuracy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        print(f"✅ 결과 저장: {filename}")


if __name__ == "__main__":
    asyncio.run(main())

