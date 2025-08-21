import os
import importlib
from typing import Dict, Any, Optional


class PromptManager:
    def __init__(self, base_path: str = "prompts"):
        self.base_path = base_path
        self.prompts = {}
        self.load_all_prompts()
    
    def load_all_prompts(self):
        """모든 프롬프트 모듈을 동적으로 로드"""
        try:
            # base 모듈 로드
            base_module = importlib.import_module('llm_service.prompts.base.system_prompts')
            self.prompts['base'] = {
                'system': getattr(base_module, 'SYSTEM_BASE', ''),
                'style': getattr(base_module, 'CONVERSATION_STYLE', ''),
                'safety': getattr(base_module, 'SAFETY_FIRST_PRINCIPLE', '')
            }
            
            # schedule 모듈 로드
            schedule_module = importlib.import_module('llm_service.prompts.schedule.schedule_coordination')
            self.prompts['schedule'] = {
                'analysis': getattr(schedule_module, 'SCHEDULE_ANALYSIS_PROMPT', ''),
                'conflict': getattr(schedule_module, 'CONFLICT_RESOLUTION_PROMPT', ''),
                'optimization': getattr(schedule_module, 'SCHEDULE_OPTIMIZATION_PROMPT', '')
            }
            
            # safety 모듈 로드
            safety_module = importlib.import_module('llm_service.prompts.safety.gps_alerts')
            self.prompts['safety'] = {
                'gps_alerts': getattr(safety_module, 'GPS_SAFETY_ALERT_PROMPT', ''),
                'emergency': getattr(safety_module, 'EMERGENCY_PROTOCOL_PROMPT', '')
            }
            
            # community 모듈 로드
            community_module = importlib.import_module('llm_service.prompts.community.group_management')
            self.prompts['community'] = {
                'welcome': getattr(community_module, 'COMMUNITY_WELCOME_PROMPT', ''),
                'group_formation': getattr(community_module, 'GROUP_FORMATION_PROMPT', ''),
                'mediation': getattr(community_module, 'CONFLICT_MEDIATION_PROMPT', '')
            }
            
        except ImportError as e:
            print(f"프롬프트 모듈 로드 실패: {e}")
    
    def get_prompt(self, category: str, prompt_name: str) -> str:
        """특정 프롬프트 반환"""
        return self.prompts.get(category, {}).get(prompt_name, "")
    
    def build_system_prompt(self, context: str = "general") -> str:
        """상황별 시스템 프롬프트 조합"""
        base_prompt = self.get_prompt('base', 'system')
        style_prompt = self.get_prompt('base', 'style')
        safety_prompt = self.get_prompt('base', 'safety')
        
        system_prompt = f"{base_prompt}\n\n{style_prompt}\n\n{safety_prompt}"
        
        if context == "schedule":
            schedule_prompt = self.get_prompt('schedule', 'analysis')
            system_prompt += f"\n\n{schedule_prompt}"
        elif context == "safety":
            safety_alert_prompt = self.get_prompt('safety', 'gps_alerts')
            system_prompt += f"\n\n{safety_alert_prompt}"
        elif context == "community":
            community_prompt = self.get_prompt('community', 'welcome')
            system_prompt += f"\n\n{community_prompt}"
            
        return system_prompt
    
    def format_prompt(self, template: str, **kwargs) -> str:
        """프롬프트 템플릿에 변수 삽입"""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            print(f"템플릿 변수 누락: {e}")
            return template

# 싱글톤 인스턴스
prompt_manager = PromptManager()

# 편의 함수들
def get_system_prompt(context: str = "general") -> str:
    """시스템 프롬프트 조합"""
    return prompt_manager.build_system_prompt(context)

def get_prompt(category: str, name: str) -> str:
    """특정 프롬프트 가져오기"""
    return prompt_manager.get_prompt(category, name)

def format_prompt(template: str, **kwargs) -> str:
    """프롬프트 포맷팅"""
    return prompt_manager.format_prompt(template, **kwargs)