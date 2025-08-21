import os
import sys
import asyncio
from typing import Dict, Any
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.prompt_service import prompt_service_instance

try:
    from prompts.utils.prompt_loader import get_system_prompt, get_prompt, format_prompt
except ImportError:
    print("프롬프트 모듈을 찾을 수 없습니다. 프로젝트 루트에 prompts 폴더가 있는지 확인해주세요.")
    # 임시 대체 함수들
    def get_system_prompt(context="general"):
        return "당신은 함께 키즈 AI 어시스턴트입니다."
    
    def get_prompt(category, name):
        return ""
    
    def format_prompt(template, **kwargs):
        return template

class AIScheduleCoordinator:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.prompt_service = prompt_service_instance
        print("✅ OpenAI 클라이언트 및 PromptService 초기화 완료")
    
    
    async def test_connection(self) -> Dict[str, Any]:
        """OpenAI API 연결 테스트"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 연결 테스트를 위한 AI입니다."},
                    {"role": "user", "content": "안녕하세요! 연결 테스트입니다."}
                ],
                max_tokens=50
            )
            
            return {
                "status": "success",
                "message": "OpenAI API 연결 성공!",
                "response": response.choices[0].message.content
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"OpenAI API 연결 실패: {str(e)}"
            }
    
    async def coordinate_schedule(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """일정 조율 처리"""
        try:
            system_prompt_dict = self.prompt_service.get_system_prompt("schedule")
            system_prompt_content = system_prompt_dict["content"]
            user_message = f"""
            등하원 일정 조율을 요청합니다.
            요청 정보: {schedule_data}

            다음 형식으로 응답해주세요:
            1. 현재 상황 분석
            2. 추천 해결책 (1순위)
            3. 대안 시나리오 2개
            4. 주의사항
            """
            
            messages = [
                {"role": "system", "content": system_prompt_content},
                {"role": "user", "content": user_message}
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return {
                "status": "success",
                "coordination_result": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"일정 조율 실패: {str(e)}"
            }
    
    async def handle_safety_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """안전 알림 처리"""
        try:
            system_prompt_dict = self.prompt_service.get_system_prompt("safety")
            system_prompt_content = system_prompt_dict["content"]
            
            user_message = f"""
            GPS 안전 알림을 생성해주세요.
            알림 정보: {alert_data}
            """
            
            messages = [
                {"role": "system", "content": system_prompt_content},
                {"role": "user", "content": user_message}
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.3,  # 안전 관련은 더 일관된 응답
                max_tokens=500
            )
            
            return {
                "status": "success",
                "alert_message": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"안전 알림 처리 실패: {str(e)}"
            }

# 테스트 함수
async def test_ai_coordinator():
    """AI 코디네이터 테스트"""
    print("🚀 AI 코디네이터 테스트 시작...")
    
    coordinator = AIScheduleCoordinator()
    
    # 1. 연결 테스트
    print("1️⃣ OpenAI API 연결 테스트...")
    connection_result = await coordinator.test_connection()
    print(f"결과: {connection_result}")
    
    if connection_result["status"] == "success":
        # 2. 일정 조율 테스트
        print("\n2️⃣ 일정 조율 기능 테스트...")
        test_schedule = {
            "parent_name": "김지연엄마",
            "child_name": "김지연",
            "child_age": 5,
            "kindergarten": "행복어린이집",
            "request": "내일 오후 3시 하원인데 회사 회의가 5시까지 있어서 픽업이 어려워요. 도움 받을 수 있을까요?",
            "preferred_time": "15:00",
            "location": "행복마을 아파트 단지"
        }
        
        schedule_result = await coordinator.coordinate_schedule(test_schedule)
        print(f"일정 조율 결과: {schedule_result}")
        
        # 3. 안전 알림 테스트
        print("\n3️⃣ 안전 알림 기능 테스트...")
        test_alert = {
            "child_name": "김지연",
            "alert_type": "경로 이탈",
            "current_location": "서울시 강남구 역삼동 123-45",
            "expected_route": "어린이집 → 행복마을 아파트",
            "guardian": "변우석엄마",
            "time": "2025-08-15 15:30"
        }
        
        alert_result = await coordinator.handle_safety_alert(test_alert)
        print(f"안전 알림 결과: {alert_result}")
    
    print("\n✅ AI 코디네이터 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(test_ai_coordinator())