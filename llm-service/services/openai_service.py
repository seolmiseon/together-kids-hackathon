
import os
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.chat_model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    
    async def generate_chat_response(self, messages: List[Dict[str, str]]) -> str:
        """채팅 응답 생성"""
        try:
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"OpenAI 채팅 응답 생성 오류: {e}")
            return "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """텍스트 임베딩 생성"""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            return [data.embedding for data in response.data]
        
        except Exception as e:
            print(f"OpenAI 임베딩 생성 오류: {e}")
            return []
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """단일 텍스트 임베딩 생성"""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=[text]
            )
            return response.data[0].embedding
        
        except Exception as e:
            print(f"OpenAI 단일 임베딩 생성 오류: {e}")
            return []
    
    async def emergency_assessment(self, message: str) -> str:
        """응급 상황 1차 판단"""
        try:
            emergency_prompt = f"""
당신은 응급의학 전문가입니다. 다음 상황을 분석하고 응급도를 판단해주세요.

상황: {message}

다음 형식으로 답변해주세요:
- 응급도: [즉시 응급실/병원 방문 권장/경과 관찰]
- 이유: [판단 근거]
- 즉시 조치: [응급처치 방법]
- 주의사항: [보호자가 알아야 할 사항]

※ 생명에 위험할 수 있는 상황이면 반드시 '즉시 119 신고' 를 포함해주세요.
"""
            
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[{"role": "user", "content": emergency_prompt}],
                temperature=0.3,  # 응급 상황이므로 창의성보다 정확성 중시
                max_tokens=500
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
                                "text": f"응급 상황 이미지를 분석해주세요. 상황: {context}\n\n이미지에서 보이는 증상을 분석하고 응급도를 판단해주세요."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.3,
                max_tokens=400
            )
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"응급 이미지 분석 오류: {e}")
            return "이미지 분석 중 오류가 발생했습니다. 응급 상황이 의심되면 즉시 병원에 가세요."
