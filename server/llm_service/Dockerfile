FROM python:3.11-slim

WORKDIR /app

# requirements.txt 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# LLM 서비스 파일만 복사 (backend 제외)
COPY llm_service/ ./llm_service/
COPY serviceAccountKey.json .
COPY .env .

# LLM 서비스 실행
CMD ["uvicorn", "llm_service.main:app", "--host", "0.0.0.0", "--port", "8002"]