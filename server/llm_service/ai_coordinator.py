import os
import sys
from typing import Dict, Any
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_service.prompts.utils.prompt_loader import prompt_manager, get_system_prompt

class AIScheduleCoordinator:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.prompt_manager = prompt_manager
        print("✅ OpenAI 클라이언트 및 PromptManager 초기화 완료")
    
    
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
            system_prompt_content = get_system_prompt("schedule")
            user_message = f"""
            등하원 일정 조율을 요청합니다.
            요청 정보: {schedule_data}

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
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"일정 조율 실패: {str(e)}"
            }
    
    async def handle_safety_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """안전 알림 처리"""
        try:
            system_prompt_content = get_system_prompt("safety")
            
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
                "alert_message": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"안전 알림 처리 실패: {str(e)}"
            }

