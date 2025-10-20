import os
import importlib
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PromptManager:
    def __init__(self, base_path: str = "prompts"):
        self.base_path = base_path
        self.prompts = {}
        logger.info("PromptManager 초기화 시작")
        self.load_all_prompts()
        self._validate_critical_prompts()

    def load_all_prompts(self):
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

            # place 모듈 로드
            try:
                place_module = importlib.import_module('llm_service.prompts.place.place_prompts')
                self.prompts['place'] = {
                    'system': getattr(place_module, 'PLACE_RECOMMENDATION_SYSTEM', ''),
                    'naming': getattr(place_module, 'PLACE_NAMING_STRICT_RULES', ''),
                    'enhancement': ''
                }
                logger.info("✅ place 프롬프트 로드 완료")
            except ImportError as e:
                logger.warning(f"⚠️ place 프롬프트 로드 실패: {e}")
                self.prompts['place'] = {
                    'system': '장소 추천 시 구체적인 실제 장소명을 사용하고, 자리표시자(○○, XX)는 절대 사용하지 마세요.',
                    'naming': '네이버 지도에서 검색 가능한 정확한 장소명으로만 추천해주세요.',
                    'enhancement': '실제 검색 결과 데이터를 최우선으로 활용하여 정확한 정보를 제공해주세요.'
                }

            # emotion 모듈 로드
            try:
                emotion_module = importlib.import_module('llm_service.prompts.emotion.emotion_analysis')
                self.prompts['emotion'] = {
                    'basic': getattr(emotion_module, 'BASIC_EMOTION_PROMPT', ''),
                    'community_matching': getattr(emotion_module, 'COMMUNITY_MATCHING_EMOTION', ''),
                    'intensity': getattr(emotion_module, 'EMOTION_INTENSITY_PROMPT', '')
                }
                logger.info("✅ emotion 프롬프트 로드 완료")
            except ImportError:
                # emotion만 실패했을 때 기본값 제공
                self.prompts['emotion'] = {
                    'basic': '육아 부모의 감정 상태를 분석하여 적절한 지원을 제공해주세요.',
                    'community_matching': '감정 상태를 기반으로 적합한 육아 커뮤니티를 추천해주세요.',
                    'intensity': '육아 스트레스 강도를 1-5단계로 측정해주세요.'
                }
                logger.warning("⚠️ emotion 프롬프트 기본값 사용")

        except ImportError as e:
            logger.error(f"❌ 프롬프트 모듈 로드 실패: {e}")

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
        elif context == "emotion":
            emotion_prompt = self.get_prompt('emotion', 'basic')
            system_prompt += f"\n\n{emotion_prompt}"
        elif context == "place":
            place_prompt = self.get_prompt('place', 'system')
            naming_prompt = self.get_prompt('place', 'naming')
            system_prompt += f"\n\n{place_prompt}\n\n{naming_prompt}"
        elif context == "community_emotion":
            community_prompt = self.get_prompt('community', 'welcome')
            emotion_prompt = self.get_prompt('emotion', 'community_matching')
            system_prompt += f"\n\n{community_prompt}\n\n{emotion_prompt}"

        return system_prompt

    def format_prompt(self, template: str, **kwargs) -> str:
        """프롬프트 템플릿에 변수 삽입"""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            print(f"템플릿 변수 누락: {e}")
            return template

    def _validate_critical_prompts(self):
        # 구현 필요시 여기에 작성
        pass

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
