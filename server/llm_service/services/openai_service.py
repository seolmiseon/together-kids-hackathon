import os
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
from .prompt_service import PromptService

load_dotenv()
client = OpenAI()


class OpenAIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

        self.client = OpenAI(api_key=api_key)
        self.chat_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.embedding_model = os.getenv(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        )
        self.prompt_service = PromptService()

    async def generate_chat_response(self, messages: List[Dict[str, str]]) -> str:
        """채팅 응답 생성"""
        try:
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"OpenAI 채팅 응답 생성 오류: {e}")
            return "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """텍스트 임베딩 생성"""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model, input=texts
            )
            return [data.embedding for data in response.data]

        except Exception as e:
            print(f"OpenAI 임베딩 생성 오류: {e}")
            return []

    async def generate_single_embedding(self, text: str) -> List[float]:
        """단일 텍스트 임베딩 생성"""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model, input=[text]
            )
            return response.data[0].embedding

        except Exception as e:
            print(f"OpenAI 단일 임베딩 생성 오류: {e}")
            return []

    async def emergency_assessment(self, message: str) -> str:
        """응급 상황 1차 판단"""
        try:
            # 동적 프롬프트 생성 (기존 시스템 활용)
            emergency_prompt_template = self.prompt_service.manager.get_prompt(
                "gps_alerts", "EMERGENCY_ASSESSMENT_PROMPT"
            )
            emergency_prompt = emergency_prompt_template.format(situation=message)

            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[{"role": "user", "content": emergency_prompt}],
                temperature=0.3,  # 응급 상황이므로 창의성보다 정확성 중시
                max_tokens=500,
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"응급 상황 판단 오류: {e}")
            return "응급 상황 판단 중 오류가 발생했습니다. 의심스러우면 즉시 119에 신고하세요."

    async def analyze_image_emergency(self, image_data: bytes, context: str) -> str:
        """응급 상황 이미지 분석"""
        try:
            import base64

            # 이미지를 base64로 인코딩
            base64_image = base64.b64encode(image_data).decode()

            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"응급 상황 이미지를 분석해주세요. 상황: {context}\n\n이미지에서 보이는 증상을 분석하고 응급도를 판단해주세요.",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                temperature=0.3,
                max_tokens=400,
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"응급 이미지 분석 오류: {e}")
            return "이미지 분석 중 오류가 발생했습니다. 응급 상황이 의심되면 즉시 병원에 가세요."
