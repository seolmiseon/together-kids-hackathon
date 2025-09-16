'use client';

import { useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { getAuth, signInWithCustomToken } from 'firebase/auth';
import { useUserStore } from '@/store/userStore';

function NaverCallbackContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const { handleSocialLoginComplete } = useUserStore();

    useEffect(() => {
        if (code) {
            const processNaverLogin = async (authCode: string) => {
                try {
                    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
                    const response = await fetch(`${apiUrl}/auth/firebase/naver`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            code: authCode,
                            state: state,
                        }),
                    });

                    if (!response.ok) {
                        throw new Error('Firebase 토큰 교환에 실패했습니다.');
                    }

                    const { firebase_token } = await response.json();

                    const auth = getAuth();
                    await signInWithCustomToken(auth, firebase_token);
                    console.log('✅ 네이버 Firebase 로그인 성공');

                    // 🚀 Zustand 공통 처리
                    await handleSocialLoginComplete(router);
                    
                } catch (error) {
                    console.error('네이버 로그인 콜백 처리 중 오류:', error);
                    router.replace('/auth/login');
                }
            };

            processNaverLogin(code);
        }
    }, [code, state, router, handleSocialLoginComplete]);

    return (
        <div className="flex items-center justify-center min-h-screen">
            <p>네이버 로그인 처리 중...</p>
        </div>
    );
}

export default function NaverCallbackPage() {
    return (
        <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><p>로딩 중...</p></div>}>
            <NaverCallbackContent />
        </Suspense>
    );
}
