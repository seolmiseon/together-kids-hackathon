'use client';

import { useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { getAuth, signInWithCustomToken } from 'firebase/auth';

export default function NaverCallbackPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const code = searchParams.get('code');
    const state = searchParams.get('state');

    useEffect(() => {
        if (code) {
            const exchangeCodeForFirebaseToken = async (authCode: string) => {
                try {
                    // 1. 백엔드에 인증 코드를 보내 Firebase 커스텀 토큰을 요청합니다.
                    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
                    const response = await fetch(
                        `${apiUrl}/auth/firebase/naver`,
                        {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                code: authCode,
                                state: state,
                            }), // 백엔드에 code와 state를 전달합니다.
                        }
                    );

                    if (!response.ok) {
                        throw new Error('Firebase 토큰 교환에 실패했습니다.');
                    }

                    const { firebase_token } = await response.json();

                    // 2. 받은 커스텀 토큰으로 Firebase에 로그인합니다.
                    const auth = getAuth();
                    await signInWithCustomToken(auth, firebase_token);
                    console.log('✅ Firebase 로그인 성공');

                    // 3. 사용자 프로필 확인
                    const user = auth.currentUser;
                    if (user) {
                        const token = await user.getIdToken();

                        // 사용자 프로필 상태 확인
                        const profileResponse = await fetch(
                            `${apiUrl}/users/profile`,
                            {
                                headers: {
                                    Authorization: `Bearer ${token}`,
                                    'Content-Type': 'application/json',
                                },
                            }
                        );

                        if (profileResponse.ok) {
                            const profileData = await profileResponse.json();

                            // 프로필이 완성되어 있는지 확인 (자녀 정보 포함)
                            if (
                                profileData.full_name &&
                                profileData.apartment_complex
                            ) {
                                // 자녀 정보도 확인
                                const childrenResponse = await fetch(
                                    `${apiUrl}/children/`,
                                    {
                                        headers: {
                                            Authorization: `Bearer ${token}`,
                                            'Content-Type': 'application/json',
                                        },
                                    }
                                );

                                if (childrenResponse.ok) {
                                    const childrenData =
                                        await childrenResponse.json();

                                    if (
                                        childrenData.children &&
                                        childrenData.children.length > 0
                                    ) {
                                        // 프로필과 자녀 정보 모두 있음 → 대시보드로
                                        console.log(
                                            '✅ 완전한 프로필 확인 → 대시보드로 이동'
                                        );
                                        router.replace('/dashboard');
                                    } else {
                                        // 자녀 정보가 없음 → 프로필 설정으로
                                        console.log(
                                            '⚠️ 자녀 정보 없음 → 프로필 설정으로 이동'
                                        );
                                        router.replace('/auth/profile');
                                    }
                                } else {
                                    // 자녀 정보 조회 실패 → 프로필 설정으로
                                    console.log(
                                        '⚠️ 자녀 정보 조회 실패 → 프로필 설정으로 이동'
                                    );
                                    router.replace('/auth/profile');
                                }
                            } else {
                                // 기본 프로필 정보가 없음 → 프로필 설정으로
                                console.log(
                                    '⚠️ 기본 프로필 정보 없음 → 프로필 설정으로 이동'
                                );
                                router.replace('/auth/profile');
                            }
                        } else {
                            // 프로필 조회 실패 → 프로필 설정으로
                            console.log(
                                '⚠️ 프로필 조회 실패 → 프로필 설정으로 이동'
                            );
                            router.replace('/auth/profile');
                        }
                    } else {
                        // 사용자 정보 없음 → 로그인으로
                        console.log('❌ 사용자 정보 없음 → 로그인으로 이동');
                        router.replace('/auth/login');
                    }
                } catch (error) {
                    console.error('네이버 로그인 콜백 처리 중 오류:', error);
                    // 에러 발생 시 로그인 페이지로 돌려보냅니다.
                    router.replace('/auth/login');
                }
            };

            exchangeCodeForFirebaseToken(code);
        }
    }, [code, state, router]);

    return (
        <div className="flex items-center justify-center min-h-screen">
            <p>네이버 로그인 처리 중...</p>
        </div>
    );
}
