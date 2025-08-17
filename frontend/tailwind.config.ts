import type { Config } from 'tailwindcss';

const config: Config = {
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            // 이 곳에 '함께 키즈'만의 디자인 시스템을 정의합니다.
            colors: {
                primary: {
                    blue: '#3B82F6', // 신뢰감
                },
                secondary: {
                    orange: '#F59E0B', // 활동성
                },
                success: '#10B981', // 안전
                warning: '#FBBF24', // 주의
                error: '#EF4444', // 긴급
            },
            fontFamily: {
                // 프리텐다드를 기본 산세리프 폰트로 지정합니다.
                sans: [
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
        },
    },
    plugins: [],
};
export default config;
