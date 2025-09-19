# GitHub Secrets 업데이트 가이드

## 🔐 필수 GitHub Secrets 확인 및 업데이트

### 1. 기존 Secrets 유지 (변경 불필요)
- `GCP_SA_KEY`: Google Cloud Service Account Key
- `GCP_PROJECT_ID`: Google Cloud Project ID  
- `SECRET_KEY`: FastAPI Secret Key
- `OPENAI_API_KEY`: OpenAI API Key
- `NEXT_PUBLIC_FIREBASE_API_KEY`: Firebase API Key
- `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`: Firebase Auth Domain
- `NEXT_PUBLIC_FIREBASE_PROJECT_ID`: Firebase Project ID
- `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET`: Firebase Storage Bucket
- `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID`: Firebase Messaging Sender ID
- `NEXT_PUBLIC_FIREBASE_APP_ID`: Firebase App ID
- `NEXT_PUBLIC_NAVER_MAP_CLIENT_ID`: Naver Map Client ID
- `FIREBASE_SERVICE_ACCOUNT_TOGATHERKIDS`: Firebase Service Account

### 2. 삭제 가능한 Secrets (더 이상 사용하지 않음)
- `NEXT_PUBLIC_API_URL`: 이제 워크플로우에서 하드코딩됨

## 🚀 업데이트 완료 후 배포 순서

1. **코드 변경사항 커밋 & 푸시**
   ```bash
   git add .
   git commit -m "feat: 통합 서비스로 워크플로우 업데이트 및 실전 배포 준비"
   git push origin main
   ```

2. **자동 배포 확인**
   - GitHub Actions에서 CI 통과 확인
   - 통합 서비스 배포 성공 확인
   - 프론트엔드 배포 성공 확인

3. **배포 검증**
   - https://togatherkids.web.app 접속 확인
   - OAuth 로그인 테스트
   - AI 채팅 기능 테스트
   - 새로운 피드백 학습 시스템 테스트

## 📝 변경 사항 요약

### 워크플로우 구조 변경
- ❌ 기존: `deploy-backend-main.yml` + `deploy-backend-llm.yml` (2개 서비스)
- ✅ 새로운: `deploy-integrated-service.yml` (1개 통합 서비스)

### API 엔드포인트 통합
- ❌ 기존: 
  - `https://hackathon-backend-xxx.run.app` (인증, 사용자 관리)
  - `https://hackathon-llm-service-xxx.run.app` (AI 채팅)
- ✅ 새로운:
  - `https://hackathon-integrated-service-529342898795.asia-northeast3.run.app` (모든 기능)

### 새로운 AI 기능 추가
- 🎯 사용자 피드백 기반 AI 학습 시스템
- 🧠 동적 프롬프트 선택 시스템
- 📊 RAG 기반 프롬프트 관리 시스템