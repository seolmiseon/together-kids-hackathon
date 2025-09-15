'use client';

import Image from 'next/image';
import {
    getAuth,
    signInWithRedirect,
    GoogleAuthProvider,
    OAuthProvider,
} from 'firebase/auth';

export default function LoginPage() {
    const handleSocialLogin = async (providerName: string) => {
        try {
            let authUrl = '';
            const baseUrl = window.location.origin;

            switch (providerName) {
                case 'google':
                    const googleClientId =
                        process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ||
                        '746400540092-eo7k6k953tfpftt9dideau65bt4cn38g.apps.googleusercontent.com';
                    authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${googleClientId}&redirect_uri=${baseUrl}/auth/callback/google&response_type=code&scope=openid%20profile%20email`;
                    break;
                case 'kakao':
                    const kakaoClientId =
                        process.env.NEXT_PUBLIC_KAKAO_CLIENT_ID ||
                        '7688b55c81dc5a35def8a4c3cf75311c';
                    authUrl = `https://kauth.kakao.com/oauth/authorize?client_id=${kakaoClientId}&redirect_uri=${baseUrl}/auth/callback/kakao&response_type=code`;
                    break;
                case 'naver':
                    const naverClientId =
                        process.env.NEXT_PUBLIC_NAVER_CLIENT_ID ||
                        'Z7kxwu972HcdvMDJMQbB';
                    const state = Math.random().toString(36).substring(7);
                    authUrl = `https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id=${naverClientId}&redirect_uri=${baseUrl}/auth/callback/naver&state=${state}`;
                    break;
                default:
                    console.error('지원하지 않는 소셜 로그인입니다.');
                    return;
            }

            window.location.href = authUrl;
        } catch (error) {
            console.error(`${providerName} 로그인 중 오류 발생:`, error);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4">
            <div className="w-full max-w-sm mx-auto text-center">
                <Image
                    src="/images/logo/logowide.png"
                    alt="함께 키즈 로고"
                    width={160}
                    height={60}
                    priority
                    className="mx-auto mb-6"
                />
                <p className="text-gray-600 mb-8 text-sm">
                    맞벌이 부모를 위한 공동육아 플랫폼
                </p>
                <div className="space-y-3">
                    <button
                        onClick={() => handleSocialLogin('kakao')}
                        className="w-full py-3 rounded-lg bg-[#FEE500] hover:bg-[#FDD800] text-gray-800 font-bold transition-colors"
                    >
                        💬 카카오로 시작하기
                    </button>
                    <button
                        onClick={() => handleSocialLogin('naver')}
                        className="w-full py-3 rounded-lg bg-[#03C75A] hover:bg-[#02B351] text-white font-bold transition-colors"
                    >
                        N 네이버로 시작하기
                    </button>
                    <button
                        onClick={() => handleSocialLogin('google')}
                        className="w-full py-3 rounded-lg bg-white hover:bg-gray-50 border border-gray-300 text-gray-700 font-bold transition-colors"
                    >
                        🔍 구글로 시작하기
                    </button>
                </div>
                <p className="text-xs text-gray-500 text-center mt-6">
                    로그인하시면 이용약관 및 개인정보처리방침에 동의하게 됩니다.
                </p>
            </div>
        </div>
    );
}
