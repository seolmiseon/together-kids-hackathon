from typing import Dict, Optional, List
from config.prompts import (
    BASE_ROLE, BASE_CONTEXT, COMMON_ROLES, SPEAKING_STYLES, 
    SPECIAL_ROLES, PROMPT_TEMPLATE
)


class PromptService:
    def __init__(self):
        # 의도별 설정 매핑
        self.intent_config = {
            "schedule": {
                "role_type": "특별 역할",
                "roles": COMMON_ROLES + SPECIAL_ROLES["schedule"],
                "speaking_style": SPEAKING_STYLES["solution_focused"]
            },
            "childcare": {
                "role_type": "전문 역할", 
                "roles": SPECIAL_ROLES["childcare"],
                "speaking_style": SPEAKING_STYLES["expert"]
            },
            "default": {
                "role_type": "역할",
                "roles": COMMON_ROLES,
                "speaking_style": SPEAKING_STYLES["friendly"]
            }
        }
    
    def _build_prompt(self, intent: str = "default", extra_instructions: Optional[str] = None) -> str:
        
        config = self.intent_config.get(intent, self.intent_config["default"])
        # 역할 목록을 문자열로 변환
        roles_text = "\n".join([f"- {role}" for role in config["roles"]])
        prompt = PROMPT_TEMPLATE.format(
            role=BASE_ROLE,
            context=BASE_CONTEXT,
            role_type=config["role_type"],
            roles=roles_text,
            speaking_style=config["speaking_style"]
        )
        
        if extra_instructions:
            prompt += f"\n\n{extra_instructions}"
        
        return prompt
        
    
    def get_system_prompt(self, intent: str = "default", context_info: Optional[str] = None) -> Dict[str, str]:
        
        base_prompt = self._build_prompt(intent)
        if context_info:
            base_prompt += context_info
        return {
            "role": "system",
            "content": base_prompt
        }
    
    def get_prompt_for_intent(self, intent: str, context_info: Optional[str] = None) -> Dict[str, str]:
        return self.get_system_prompt(intent, context_info)
    
    def add_role_for_intent(self, intent: str, new_roles: List[str]):
        if intent not in self.intent_config:
            self.intent_config[intent] = self.intent_config["default"].copy()
        self.intent_config[intent]["roles"].extend(new_roles)
    
    def get_available_intents(self) -> List[str]:
        return list(self.intent_config.keys())
