/** @type {import('next').NextConfig} */
const nextConfig = {
    // 외부 이미지 도메인 허용
    images: {
        domains: [
            'ssl.pstatic.net', // 네이버 프로필 이미지
            'lh3.googleusercontent.com', // 구글 프로필 이미지
            'k.kakaocdn.net', // 카카오 프로필 이미지
            't1.kakaocdn.net', // 카카오 프로필 이미지 (추가)
        ],
    },
    // 여기에 Next.js 관련 특별한 설정을 추가할 수 있습니다.
};

export default nextConfig;
