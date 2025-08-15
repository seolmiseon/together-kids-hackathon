# MySQL 데이터베이스 설정 가이드

## 1. MySQL 설치 (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

## 2. 데이터베이스 및 사용자 생성

```sql
-- MySQL 관리자로 로그인
sudo mysql -u root -p

-- 데이터베이스 생성
CREATE DATABASE together_kids CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 사용자 생성 및 권한 부여
CREATE USER 'together_user'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON together_kids.* TO 'together_user'@'localhost';
FLUSH PRIVILEGES;

-- 확인 및 종료
SHOW DATABASES;
EXIT;
```

## 3. 환경 변수 설정 (.env 파일)

```
# 개발환경 (SQLite)
DATABASE_URL=sqlite:///./together_kids.db

# 운영환경 (MySQL)
DATABASE_URL=mysql+pymysql://together_user:your_password_here@localhost:3306/together_kids
```

## 4. 데이터베이스 마이그레이션

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행 (자동으로 테이블 생성됨)
python main.py
```

## 5. MySQL 기본 명령어

```sql
-- 데이터베이스 선택
USE together_kids;

-- 테이블 확인
SHOW TABLES;

-- 테이블 구조 확인
DESCRIBE users;

-- 데이터 확인
SELECT * FROM users LIMIT 5;
```

## 6. 연결 테스트

```python
# 간단한 연결 테스트
from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT VERSION()"))
    print(f"MySQL 버전: {result.fetchone()[0]}")
```

## 주의사항

-   운영환경에서는 반드시 강력한 비밀번호 사용
-   정기적인 데이터베이스 백업 설정
-   MySQL 8.0 이상 권장 (utf8mb4 완전 지원)
