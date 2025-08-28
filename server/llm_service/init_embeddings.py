import os
import sys
import asyncio


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_service.services.vector_service import VectorService
from llm_service.prompts.utils.prompt_loader import prompt_manager

from llm_service.database.crud import get_all_schedules_from_firestore

async def main():
    """
    crud.py에서 데이터를 받아와 Vector DB에 임베딩하고 저장합니다.
    """
    print(" 벡터 데이터베이스 초기화를 시작합니다...")
    
    vector_service = VectorService()
    
    try:
        # --- 1. 모든 프롬프트 정보를 벡터 DB에 추가 ---
        print(" 프롬프트 데이터를 임베딩하는 중...")
        all_prompts = []
        for category, prompts in prompt_manager.prompts.items():
            for name, content in prompts.items():
                all_prompts.append({
                    "text": content,
                    "metadata": {"source": "prompt", "category": category, "name": name}
                })
        
        if all_prompts:
            await vector_service.add_documents(all_prompts)
            print(f" 프롬프트 {len(all_prompts)}개 추가 완료!")

        # --- 2. Firestore 데이터를 벡터 DB에 추가 ---
        print("\n Firestore 데이터를 임베딩하는 중...")
        # [수정] 이제 crud.py의 전문가에게 데이터만 요청하면 됩니다.
        schedules_to_add = await get_all_schedules_from_firestore()
        
        if schedules_to_add:
            await vector_service.add_documents(schedules_to_add)
            print(f" Firestore 일정 {len(schedules_to_add)}개 추가 완료!")

    except Exception as e:
        print(f" 벡터 데이터베이스 초기화 중 오류 발생: {e}")
    
    print("\n모든 임베딩 작업이 완료되었습니다!")


if __name__ == "__main__":   
    # 예: (venv) $ python -m llm_service.init_embeddings
    asyncio.run(main())
