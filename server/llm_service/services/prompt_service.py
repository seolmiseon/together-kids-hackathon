from typing import Dict, Optional
from ..prompts.utils.prompt_loader import prompt_manager

class PromptService:
    def __init__(self):
        # [업그레이드] PromptManager 인스턴스를 사용하여 모든 프롬프트를 관리합니다.
        # 이제 새로운 프롬프트 파일을 추가해도 이 코드를 수정할 필요가 없습니다.
        self.manager = prompt_manager

    def get_system_prompt(self, intent: str = "general", context_info: Optional[str] = None) -> Dict[str, str]:
        """
        주어진 의도(intent)에 따라 최종 시스템 프롬프트를 생성합니다.
        """
        # 1. AI의 기본 정체성(base) 프롬프트를 가져옵니다.
        base_prompt = self.manager.get_prompt('base', 'system')
        style_prompt = self.manager.get_prompt('base', 'style')
        safety_prompt = self.manager.get_prompt('base', 'safety')

        final_prompt = f"{base_prompt}\n\n{style_prompt}\n\n{safety_prompt}"

        # 2. 대화의 의도(intent)에 맞는 전문 프롬프트를 동적으로 찾아 추가합니다.
        # 예: intent가 'schedule'이면 'schedule' 카테고리의 모든 프롬프트를 추가합니다.
        specific_prompts = self.manager.prompts.get(intent)
        if specific_prompts:
            final_prompt += f"\n\n### '{intent}' 작업에 대한 특별 지침:\n"
            for key, prompt_text in specific_prompts.items():
                final_prompt += f"\n--- {key.upper()} ---\n{prompt_text}"

        # 3. 실시간 참고 정보(RAG 검색 결과 등)가 있다면 추가합니다.
        if context_info:
            final_prompt += "\n\n### 추가 참고 정보:\n"
            final_prompt += context_info
            
        return {
            "role": "system",
            "content": final_prompt
        }

    def get_prompt_for_intent(self, intent: str, context_info: Optional[str] = None) -> Dict[str, str]:
        """get_system_prompt의 별칭으로, 일관된 인터페이스를 제공합니다."""
        return self.get_system_prompt(intent, context_info)

# 서비스 인스턴스 생성 (싱글톤)
# 다른 파일에서는 이 prompt_service_instance를 import하여 사용합니다.
prompt_service_instance = PromptService()
