# GCP Cloud SQL 연동 가이드

## 1. GCP Cloud SQL MySQL 인스턴스 생성

```bash
# gcloud CLI 사용
gcloud sql instances create together-kids-mysql \
    --database-version=MYSQL_8_0 \
    --tier=db-f1-micro \
    --region=asia-northeast3
```

## 2. 데이터베이스 및 사용자 생성

```bash
# 데이터베이스 생성
gcloud sql databases create together_kids --instance=together-kids-mysql

# 사용자 생성
gcloud sql users create together_user --instance=together-kids-mysql --password=your_secure_password
```

## 3. 연결 설정

### A. 공개 IP 연결 (개발용)

```bash
# 현재 IP 허용
gcloud sql instances patch together-kids-mysql \
    --authorized-networks=$(curl -s https://ipinfo.io/ip)/32
```

### B. Private IP 연결 (운영용)

```bash
# VPC 피어링 설정
gcloud services vpc-peerings connect \
    --service=servicenetworking.googleapis.com \
    --ranges=google-managed-services-default \
    --network=default
```

## 4. 환경 변수 설정

```bash
# .env 파일
DATABASE_URL=mysql+pymysql://together_user:your_password@PUBLIC_IP:3306/together_kids

# 또는 Cloud SQL Proxy 사용시
DATABASE_URL=mysql+pymysql://together_user:your_password@127.0.0.1:3306/together_kids
```

## 5. Cloud SQL Proxy 사용 (권장)

```bash
# Cloud SQL Proxy 다운로드
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy

# 실행 (백그라운드)
./cloud_sql_proxy -instances=PROJECT_ID:REGION:together-kids-mysql=tcp:3306 &
```

## 6. Docker에서 GCP Cloud SQL 연결

```dockerfile
# Dockerfile에 Cloud SQL Proxy 추가
FROM python:3.11-slim

# Cloud SQL Proxy 설치
RUN wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O /usr/local/bin/cloud_sql_proxy
RUN chmod +x /usr/local/bin/cloud_sql_proxy

# 시작 스크립트
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
```

```bash
# start.sh
#!/bin/bash
# Cloud SQL Proxy 시작
/usr/local/bin/cloud_sql_proxy -instances=$INSTANCE_CONNECTION_NAME=tcp:3306 &

# 애플리케이션 시작
python main.py
```

## 7. GCP Console에서 관리

-   **웹 UI**: https://console.cloud.google.com/sql
-   **쿼리 실행**: Cloud Shell이나 Cloud SQL 쿼리 편집기 사용
-   **모니터링**: CPU, 메모리, 연결 수 실시간 확인

## 비용 최적화

-   **db-f1-micro**: 무료 티어 (소규모 개발용)
-   **자동 백업**: 필요시에만 활성화
-   **연결 풀링**: SQLAlchemy 연결 풀 설정
