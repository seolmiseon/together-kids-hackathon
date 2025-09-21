FROM python:3.11-slim


WORKDIR /app

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 의존성 복사 및 설치
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . /app

# 포트 노출 (Cloud Run 기본 포트)
EXPOSE 8080

# 컨테이너 시작 시 실행할 명령어 (통합 서비스 실행)
CMD ["python", "main.py"]