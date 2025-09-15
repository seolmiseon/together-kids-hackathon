'use client';

import { useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { getAuth, signInWithCustomToken } from 'firebase/auth';
import { useUserStore } from '@/store/userStore';

function KakaoCallbackContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const code = searchParams.get('code');
    const { handleSocialLoginComplete } = useUserStore();

    useEffect(() => {
        if (code) {
            const processKakaoLogin = async (authCode: string) => {
                try {
                    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
                    const response = await fetch(`${apiUrl}/auth/firebase/kakao/`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ code: authCode }),
                    });

                    if (!response.ok) {
                        throw new Error('Firebase 토큰 교환에 실패했습니다.');
                    }

                    const { firebase_token } = await response.json();

                    const auth = getAuth();
                    await signInWithCustomToken(auth, firebase_token);
                    console.log('✅ 카카오 Firebase 로그인 성공');

                    // 🚀 Zustand 공통 처리
                    await handleSocialLoginComplete(router);
                    
                } catch (error) {
                    console.error('카카오 로그인 콜백 처리 중 오류:', error);
                    router.replace('/auth/login');
                }
            };

            processKakaoLogin(code);
        }
    }, [code, router, handleSocialLoginComplete]);

    return (
        <div className="flex items-center justify-center min-h-screen">
            <p>카카오 로그인 처리 중...</p>
        </div>
    );
}

export default function KakaoCallbackPage() {
    return (
        <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><p>로딩 중...</p></div>}>
            <KakaoCallbackContent />
        </Suspense>
    );
}
