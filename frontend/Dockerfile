FROM node:20-alpine AS builder

WORKDIR /app

# 의존성 설치
COPY package*.json ./
RUN npm ci

# 소스 코드 복사 및 빌드
COPY . .
RUN npm run build

# 프로덕션 런타임
FROM node:20-alpine AS runner

WORKDIR /app

# 환경 변수 설정
ENV NODE_ENV=production

# 사용자 생성 (보안)
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 필요한 파일만 선택적 복사
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public/images ./public/images     
COPY --from=builder /app/public/favicon.ico ./public/      
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# 권한 설정
USER nextjs

# 포트 노출
EXPOSE 3000

# 실행
CMD ["npm", "start"]