# 함께키즈 (Together Kids)

> 아파트 단지 내 맞벌이 부모들의 공동육아를 돕는 AI 기반 플랫폼

## 프로젝트 개요

함께키즈는 아파트 단지 내 부모들이 서로 도우며 아이를 키울 수 있도록 돕는 종합 육아 플랫폼입니다.

### 핵심 기능

-   **AI 육아 도우미**: OpenAI GPT-4o-mini 기반 24시간 상담
-   **실시간 위치 공유**: 네이버 지도 API 연동 위치 서비스
-   **스마트 장소 검색**: AI 기반 주변 키즈 카페, 놀이터 추천
-   **일정 관리**: 아이 스케줄 및 예방접종 알림
-   **커뮤니티**: 아파트 내 육아 정보 공유
-   **안전한 인증**: Firebase Auth 기반 보안 시스템

## 아키텍처

```
┌─────────────────┬─────────────────┬─────────────────┐
│   Frontend      │   LLM Service   │  Main Backend   │
│   (Next.js)     │   (Port 8002)   │   (Port 8000)   │
├─────────────────┼─────────────────┼─────────────────┤
│ React UI        │ AI 채팅         │ 사용자 관리      │
│ 네이버 지도      │ RAG 검색        │ 아이 프로필      │
│ 모바일 최적화    │ 장소 검색       │ 일정 관리        │
│ Firebase        │ 프롬프트 AI     │ 인증/권한        │
└─────────────────┴─────────────────┴─────────────────┘
                            ↓
                    Firestore Database
```

## 기술 스택

### Frontend

-   **Next.js 14** - React 기반 풀스택 프레임워크
-   **TypeScript** - 타입 안전성
-   **Tailwind CSS** - 유틸리티 기반 스타일링
-   **Firebase Auth** - 소셜 로그인 (Google, Kakao,Naver)
-   **Naver Maps API** - 실시간 위치 서비스

### Backend

-   **FastAPI** - 고성능 Python 웹 프레임워크
-   **SQLAlchemy** - ORM 데이터베이스 관리
-   **Firestore** - NoSQL 실시간 데이터베이스
-   **OpenAI GPT-4o-mini** - AI 언어 모델
-   **Naver Search API** - 장소 검색 서비스

### Infrastructure

-   **Docker** - 컨테이너화
-   **GCP Cloud Run** - 서버리스 배포
-   **Firestore** - NoSQL 실시간 데이터베이스 및 세션 관리
-   **Firebase Auth** - 사용자 인증 및 세션 관리

## 폴더 구조

```
hackathon/
├── docs/              # 프로젝트 문서 (PPT HTML)
├── frontend/          # Next.js 프론트엔드
│   ├── src/app/       # Next.js 앱 라우터
│   ├── src/components/# React 컴포넌트
│   ├── src/store/     # 상태 관리 (Zustand)
│   └── public/        # 정적 파일
├── server/            # 백엔드 서비스들
│   ├── backend/       # FastAPI 메인 백엔드
│   ├── llm_service/   # AI 채팅 서비스
│   └── docker-compose.yml
└── README.md
```

## 개발 상태

### 완료된 작업

-   [x] 프로젝트 기획 및 아키텍처 설계
-   [x] LLM Service 구현
    -   [x] OpenAI GPT-4o-mini 연동
    -   [x] UnifiedChatService (RAG + Community 통합)
    -   [x] Firebase 기반 세션 관리
    -   [x] 동적 프롬프트 시스템
    -   [x] 벡터 검색 RAG 구현
    -   [x] 네이버 장소 검색 API 연동
-   [x] Main Backend API 구현
    -   [x] JWT 인증 시스템
    -   [x] 사용자 관리 (회원가입/로그인)
    -   [x] 아이 프로필 관리
    -   [x] 일정 관리 시스템
    -   [x] LLM 서비스 연동
-   [x] 데이터베이스 설계
    -   [x] Firestore NoSQL 데이터베이스 구조 설계
    -   [x] Firebase Auth 사용자 관리
    -   [x] 실시간 데이터 동기화 구현
-   [x] 개발환경 구축
    -   [x] Docker Compose 설정
    -   [x] Firebase 프로젝트 설정
    -   [x] GCP Cloud Run 배포 가이드

### 진행 예정 작업

-   [x] Frontend 개발
    -   [x] React/Next.js 프로젝트 구현 완료
    -   [x] AI 채팅 UI 컴포넌트
    -   [x] Firebase 인증 시스템
    -   [x] 네이버 지도 연동
    -   [x] 실시간 위치 공유
    -   [x] AI 장소 검색 기능
    -   [x] 사용자 프로필 관리
    -   [x] 아이 프로필 관리 페이지
    -   [ ] 일정 캘린더 인터페이스
    -   [ ] 커뮤니티 게시판
-   [x] **모바일 최적화**
    -   [x] 반응형 디자인 개선
    -   [x] 터치 인터페이스 최적화
    -   [x] PWA 기능 구현
    -   [x] 모바일 성능 최적화
-   [x] 추가 기능 구현
    -   [x] AI 기반 장소 검색 및 지도 표시
    -   [x] 실시간 위치 마커 표시
    -   [x] 네이버 지도 연동 네비게이션
    -   [x] 실시간 알림 시스템
    -   [ ] 아파트별 커뮤니티 관리
    -   [x] 일정 알림 기능
-   [ ] 배포 및 운영
    -   [x] GCP Cloud Run 배포
    -   [x] MySQL 운영 DB 설정
    -   [ ] 도메인 및 SSL 인증서
    -   [ ] 모니터링 및 로깅

## GCP Cloud Run 배포

### 1. 프로젝트 설정

```bash
# Google Cloud CLI 설치 및 로그인
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Container Registry 활성화
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com
```

### 2. 백엔드 배포

```bash
# 메인 백엔드 이미지 빌드 및 푸시
cd server
docker build -f Dockerfile -t gcr.io/YOUR_PROJECT_ID/together-kids-backend .
docker push gcr.io/YOUR_PROJECT_ID/together-kids-backend

# Cloud Run 배포
gcloud run deploy together-kids-backend \
  --image gcr.io/YOUR_PROJECT_ID/together-kids-backend \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10
```

### 3. LLM 서비스 배포

```bash
# LLM 서비스 이미지 빌드 및 푸시
cd server
docker build -f llm_service/Dockerfile -t gcr.io/YOUR_PROJECT_ID/together-kids-llm .
docker push gcr.io/YOUR_PROJECT_ID/together-kids-llm

# Cloud Run 배포
gcloud run deploy together-kids-llm \
  --image gcr.io/YOUR_PROJECT_ID/together-kids-llm \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --port 8002 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 5
```

### 4. 프론트엔드 배포 (Firebase Hosting)

```bash
# Firebase CLI 설치 및 로그인
npm install -g firebase-tools
firebase login

# 프론트엔드 빌드 및 배포
cd frontend
npm install
npm run build
firebase deploy

# 배포 완료 후 URL 확인
# https://YOUR_PROJECT_ID.web.app
```

### 5. 환경 변수 설정

```bash
# 백엔드 환경 변수
gcloud run services update together-kids-backend \
  --set-env-vars="SECRET_KEY=your_jwt_secret" \
  --set-env-vars="LLM_SERVICE_URL=https://together-kids-llm-xxx.run.app" \
  --set-env-vars="FIREBASE_PROJECT_ID=your_firebase_project_id"

# LLM 서비스 환경 변수
gcloud run services update together-kids-llm \
  --set-env-vars="OPENAI_API_KEY=your_openai_key" \
  --set-env-vars="NAVER_CLIENT_ID=your_naver_id" \
  --set-env-vars="NAVER_CLIENT_SECRET=your_naver_secret"

# 프론트엔드 환경 변수는 .env.local 파일에서 관리
# firebase.json에서 빌드 시 자동 포함됨
```

````

## 빠른 시작

### 환경 설정

```bash
git clone <repository-url>
cd hackathon

# 환경 변수 설정
cp backend/.env.example backend/.env
cp llm_service/.env.example llm_service/.env
````

### LLM 서비스 실행

```bash
cd server
source venv/bin/activate
pip install -r requirements.txt
uvicorn llm_service.main:app --reload --port 8002
# http://localhost:8002
```

### 메인 백엔드 실행

```bash
cd server
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
# http://localhost:8000
```

### 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
# http://localhost:3000
```

### Docker Compose 실행

```bash
cd server
docker-compose up -d
# 개발용 로컬 서비스들 실행
# API 문서: http://localhost:8000/docs
```

## API 엔드포인트

### LLM Service (Port 8002)

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
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
```

### Main Backend (.env)

```
SECRET_KEY=your_jwt_secret
LLM_SERVICE_URL=http://localhost:8002
FIREBASE_PROJECT_ID=your_firebase_project_id
```

### Frontend (.env.local)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_NAVER_MAP_CLIENT_ID=your_naver_map_client_id
NEXT_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
```

## 주요 특징

### 비용 최적화

-   OpenAI GPT-4o-mini 선택 (Solar 대비 3배 저렴)
-   효율적인 프롬프트 설계
-   Firebase 무료 티어 활용으로 인프라 비용 절감

### 마이크로서비스 아키텍처

-   AI 서비스와 백엔드 분리
-   독립적인 확장 가능
-   장애 격리 및 복구

### 실시간 기술 스택

-   RAG + Community를 하나의 채팅으로
-   사용자 경험 단순화
-   컨텍스트 기반 자동 모드 전환
-   Firebase 실시간 데이터베이스로 즉시 동기화
