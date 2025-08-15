# 함께키즈 (Together Kids)

> 아파트 단지 내 맞벌이 부모들의 공동육아를 돕는 AI 기반 플랫폼

## 프로젝트 개요

함께키즈는 아파트 단지 내 부모들이 서로 도우며 아이를 키울 수 있도록 돕는 AI 챗봇 서비스입니다.

-   AI 육아 상담: OpenAI GPT-4o-mini 기반 전문 상담
-   커뮤니티 연동: 아파트 내 육아 정보 공유
-   일정 관리: 아이 스케줄 및 예방접종 알림
-   아파트별 서비스: 단지별 맞춤형 정보 제공

## 아키텍처

```
┌─────────────────┬─────────────────┬─────────────────┐
│   Frontend      │   LLM Service   │  Main Backend   │
│   (Next.js)     │   (Port 8001)   │   (Port 8000)   │
├─────────────────┼─────────────────┼─────────────────┤
│ 채팅 UI         │ AI 채팅         │ 사용자 관리     │
│ 프로필 관리     │ RAG 검색        │ 아이 프로필     │
│ 일정 관리       │ 커뮤니티 통합   │ 일정 관리       │
│ 커뮤니티       │ Redis 세션      │ 인증/권한       │
└─────────────────┴─────────────────┴─────────────────┘
```

## 기술 스택

-   **Frontend**: Next.js
-   **Backend**: FastAPI, SQLAlchemy
-   **Database**: MySQL (PyMySQL)
-   **AI/LLM**: OpenAI GPT-4o-mini, Vector Search
-   **Cache**: Redis
-   **Infrastructure**: Docker, GCP Cloud SQL

## 폴더 구조

```
hackathon/
├── docs/              # 프로젝트 문서 (PPT HTML)
├── frontend/          # Next.js 프론트엔드 (예정)
├── backend/           # FastAPI 메인 백엔드
│   ├── models/        # SQLAlchemy 데이터베이스 모델
│   ├── routers/       # API 엔드포인트
│   ├── schemas/       # Pydantic 스키마
│   └── docker-compose.yml
├── llm_service/       # AI 채팅 서비스
│   ├── services/      # UnifiedChatService
│   ├── routers/       # 채팅 API
│   └── config/        # 프롬프트 설정
└── README.md
```

## 개발 상태

### 완료된 작업

-   [x] 프로젝트 기획 및 아키텍처 설계
-   [x] LLM Service 구현
    -   [x] OpenAI GPT-4o-mini 연동
    -   [x] UnifiedChatService (RAG + Community 통합)
    -   [x] Redis 세션 관리
    -   [x] 동적 프롬프트 시스템
    -   [x] 벡터 검색 RAG 구현
-   [x] Main Backend API 구현
    -   [x] JWT 인증 시스템
    -   [x] 사용자 관리 (회원가입/로그인)
    -   [x] 아이 프로필 관리
    -   [x] 일정 관리 시스템
    -   [x] LLM 서비스 연동
-   [x] 데이터베이스 설계
    -   [x] SQLAlchemy 모델 (User, Child, Schedule, Apartment, Post)
    -   [x] Pydantic 스키마
    -   [x] MySQL 연동 설정
-   [x] 개발환경 구축
    -   [x] Docker Compose 설정
    -   [x] GCP Cloud SQL 배포 가이드

### 진행 예정 작업

-   [ ] Frontend 개발
    -   [ ] React/Next.js 프로젝트 초기화
    -   [ ] 채팅 UI 컴포넌트
    -   [ ] 사용자 인증 페이지
    -   [ ] 아이 프로필 관리 페이지
    -   [ ] 일정 캘린더 인터페이스
    -   [ ] 커뮤니티 게시판
-   [ ] 추가 기능 구현
    -   [ ] 이미지 업로드 (아이 사진, 게시글)
    -   [ ] 실시간 알림 시스템
    -   [ ] 아파트별 커뮤니티 관리
    -   [ ] 일정 알림 기능
-   [ ] 배포 및 운영
    -   [ ] GCP Cloud Run 배포
    -   [ ] MySQL 운영 DB 설정
    -   [ ] 도메인 및 SSL 인증서
    -   [ ] 모니터링 및 로깅

## 빠른 시작

### 환경 설정

```bash
git clone <repository-url>
cd hackathon

# 환경 변수 설정
cp backend/.env.example backend/.env
cp llm_service/.env.example llm_service/.env
```

### LLM 서비스 실행

```bash
cd llm_service
pip install -r requirements.txt
python main.py
# http://localhost:8001
```

### 메인 백엔드 실행

```bash
cd backend
pip install -r requirements.txt
python main.py
# http://localhost:8000
```

### Docker Compose 실행

```bash
cd backend
docker-compose up -d
# MySQL + phpMyAdmin + Backend
# phpMyAdmin: http://localhost:8080
```

## API 엔드포인트

### LLM Service (Port 8001)

-   POST `/chat/unified` - 통합 AI 채팅
-   POST `/chat/ai-only` - AI 전용 모드
-   POST `/chat/community` - 커뮤니티 검색 모드
-   GET `/chat/history` - 대화 기록 조회

### Main Backend (Port 8000)

-   POST `/auth/register` - 회원가입
-   POST `/auth/login` - 로그인
-   GET `/users/profile` - 프로필 조회
-   POST `/children/` - 아이 프로필 생성
-   GET `/children/{id}/schedules` - 일정 조회

## 환경 변수

### LLM Service (.env)

```
OPENAI_API_KEY=your_openai_key
REDIS_URL=redis://localhost:6379/0
```

### Main Backend (.env)

```
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/together_kids
SECRET_KEY=your_jwt_secret
LLM_SERVICE_URL=http://localhost:8001
```

## 주요 특징

### 비용 최적화

-   OpenAI GPT-4o-mini 선택 (Solar 대비 3배 저렴)
-   효율적인 프롬프트 설계
-   Redis 캐싱으로 중복 요청 방지

### 마이크로서비스 아키텍처

-   AI 서비스와 백엔드 분리
-   독립적인 확장 가능
-   장애 격리 및 복구

### 통합 서비스

-   RAG + Community를 하나의 채팅으로
-   사용자 경험 단순화
-   컨텍스트 기반 자동 모드 전환
