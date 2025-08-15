import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Redis 클라이언트 초기화
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=REDIS_DB,
    decode_responses=True  
)


def test_redis_connection():
    try:
        pong = redis_client.ping()
        if pong:
            print("Redis 연결 성공!")
        else:
            print("Redis 연결 실패!")
    except Exception as e:
        print(f"Redis 연결 오류: {e}")

# 간단한 캐시 저장 함수 예시
def set_cache(key: str, value: str, expire_seconds: int = 3600):
    try:
        redis_client.set(name=key, value=value, ex=expire_seconds)
    except Exception as e:
        print(f"Redis 캐시 저장 실패: {e}")

# 간단한 캐시 조회 함수 예시
def get_cache(key: str):
    try:
        return redis_client.get(key)
    except Exception as e:
        print(f"Redis 캐시 조회 실패: {e}")
        return None
