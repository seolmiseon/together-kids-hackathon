/** @type {import('next').NextConfig} */
const nextConfig = {
    // 정적 export 설정
    output: 'export',
    distDir: 'out',
    trailingSlash: true,

    // 외부 이미지 도메인 허용
    images: {
        unoptimized: true, // 정적 export에서는 이미지 최적화 비활성화
        domains: [
            'ssl.pstatic.net', // 네이버 프로필 이미지
            'lh3.googleusercontent.com', // 구글 프로필 이미지
            'k.kakaocdn.net', // 카카오 프로필 이미지
            't1.kakaocdn.net', // 카카오 프로필 이미지 (추가)
        ],
    },
    // 개발 환경 최적화
    experimental: {
        optimizeCss: false,
    },
    // Fast Refresh 활성화
    reactStrictMode: true,
    // 빌드 최적화
    swcMinify: true,
};

export default nextConfig;
