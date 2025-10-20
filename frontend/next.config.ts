import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
    reactStrictMode: true, // ✅ 성능 최적화를 위해 활성화
    
    // 실험적 기능들 (성능 향상)
    experimental: {
        optimizeCss: true, // CSS 최적화
        scrollRestoration: true, // 스크롤 위치 복원
        typedRoutes: true, // 타입 안전한 라우팅
    },
    
    // 컴파일러 최적화
    compiler: {
        removeConsole: process.env.NODE_ENV === 'production', // 프로덕션에서 console 제거
    },
    
    // 이미지 최적화
    images: {
        formats: ['image/webp', 'image/avif'],
        minimumCacheTTL: 60,
        remotePatterns: [
            {
                protocol: 'https',
                hostname: '**',
            },
        ],
    },
    
    // 번들 크기 최적화
    webpack: (config, { dev, isServer }) => {
        if (!dev && !isServer) {
            // Firebase 번들 크기 최적화
            config.resolve.alias = {
                ...config.resolve.alias,
                '@firebase/app': '@firebase/app/dist/esm/index.esm.js',
                '@firebase/auth': '@firebase/auth/dist/esm/index.esm.js',
            };
        }
        return config;
    },
    
    // 성능 최적화
    poweredByHeader: false, // X-Powered-By 헤더 제거
    compress: true, // gzip 압축 활성화
};

export default nextConfig;
