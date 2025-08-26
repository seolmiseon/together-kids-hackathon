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
        const auth = getAuth();
        let provider;

        switch (providerName) {
            case 'google':
                provider = new GoogleAuthProvider();
                break;
            case 'kakao':
                provider = new OAuthProvider('oidc.kakao');
                break;
            case 'naver':
                provider = new OAuthProvider('oidc.naver');
                break;
            default:
                console.error('지원하지 않는 소셜 로그인입니다.');
                return;
        }

        try {
            await signInWithRedirect(auth, provider);
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
