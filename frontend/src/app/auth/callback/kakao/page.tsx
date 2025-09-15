'use client';

import { useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { getAuth, signInWithCustomToken } from 'firebase/auth';

function KakaoCallbackContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const code = searchParams.get('code');

    useEffect(() => {
        if (code) {
            const exchangeCodeForFirebaseToken = async (authCode: string) => {
                try {
                    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
                    const response = await fetch(
                        `${apiUrl}/auth/firebase/kakao/`,
                        {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ code: authCode }), // 백엔드는 이제 code를 받습니다.
                        }
                    );

                    if (!response.ok) {
                        throw new Error('Firebase 토큰 교환에 실패했습니다.');
                    }

                    const { firebase_token } = await response.json();

                    // 2. 받은 커스텀 토큰으로 Firebase에 로그인합니다.
                    const auth = getAuth();
                    await signInWithCustomToken(auth, firebase_token);

                    // 3. 로그인이 성공하면 대시보드로 이동합니다.
                    router.replace('/dashboard');
                } catch (error) {
                    console.error('카카오 로그인 콜백 처리 중 오류:', error);
                    // 에러 발생 시 로그인 페이지로 돌려보냅니다.
                    router.replace('/auth/login');
                }
            };

            exchangeCodeForFirebaseToken(code);
        }
    }, [code, router]);

    return (
        <div className="flex items-center justify-center min-h-screen">
            <p>카카오 로그인 처리 중...</p>
        </div>
    );
}

export default function KakaoCallbackPage() {
    return (
        <Suspense
            fallback={
                <div className="flex items-center justify-center min-h-screen">
                    <p>로딩 중...</p>
                </div>
            }
        >
            <KakaoCallbackContent />
        </Suspense>
    );
}
