import type { Config } from 'tailwindcss';

const config: Config = {
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            // ✅ 함께키즈 완전한 디자인 시스템
            colors: {
                // 브랜드 핵심 색상
                brand: {
                    primary: '#3B82F6', // 메인 파란색 (신뢰감)
                    secondary: '#F59E0B', // 서브 주황색 (활동성)
                    accent: '#10B981', // 강조 초록색 (안전)
                    dark: '#1E293B', // 다크 색상
                    light: '#F8FAFC', // 라이트 색상
                },
                // 의미론적 색상
                status: {
                    success: '#10B981', // 성공 (안전)
                    warning: '#FBBF24', // 경고 (주의)
                    error: '#EF4444', // 오류 (긴급)
                    info: '#3B82F6', // 정보
                },
                // 표면 색상 (UI 배경)
                surface: {
                    primary: '#FFFFFF',
                    secondary: '#F9FAFB',
                    tertiary: '#F3F4F6',
                    dark: '#1F2937',
                },
                // 텍스트 색상
                text: {
                    primary: '#111827',
                    secondary: '#6B7280',
                    tertiary: '#9CA3AF',
                    inverse: '#FFFFFF',
                },
            },
            fontFamily: {
                // ✅ 최적화된 폰트 스택
                sans: [
                    'Pretendard Variable',
                    'Pretendard',
                    '-apple-system',
                    'BlinkMacSystemFont',
                    'system-ui',
                    'Roboto',
                    'Helvetica Neue',  
                    'Segoe UI',
                    'Apple SD Gothic Neo',
                    'Noto Sans KR',
                    'Malgun Gothic',
                    'sans-serif',
                ],
            },
            // ✅ 성능 최적화를 위한 제한된 스페이싱
            spacing: {
                '18': '4.5rem',   // 72px
                '22': '5.5rem',   // 88px  
                '88': '22rem',    // 352px
                'safe-top': 'env(safe-area-inset-top)',
                'safe-bottom': 'env(safe-area-inset-bottom)',
                'safe-left': 'env(safe-area-inset-left)',
                'safe-right': 'env(safe-area-inset-right)',
            },
            // ✅ 애니메이션 최적화
            animation: {
                'fade-in': 'fadeIn 0.2s ease-in-out',
                'slide-up': 'slideUp 0.3s ease-out',
                'scale-in': 'scaleIn 0.2s ease-out',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { transform: 'translateY(10px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
                scaleIn: {
                    '0%': { transform: 'scale(0.95)', opacity: '0' },
                    '100%': { transform: 'scale(1)', opacity: '1' },
                },
            },
            // ✅ 그림자 최적화
            boxShadow: {
                'card': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
                'card-hover': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                'floating': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            },
        },
    },
    // ✅ 프로덕션에서 사용하지 않는 스타일 제거
    ...(process.env.NODE_ENV === 'production' && {
        purge: {
            enabled: true,
            // 항상 유지할 클래스들
            safelist: [
                'animate-pulse',
                'animate-bounce', 
                'animate-fade-in',
                'animate-slide-up',
                'animate-scale-in',
            ],
        },
    }),
    plugins: [],
};
export default config;
