'use client';

import { useEffect } from 'react';
import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, onAuthStateChanged } from 'firebase/auth';
import { useUserStore } from '@/store/userStore';
import React from 'react';

const firebaseConfig = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

export default function Providers({ children }: { children: React.ReactNode }) {
    const { login, logout } = useUserStore();

    useEffect(() => {
        // StrictMode에서 중복 실행 방지
        let isMounted = true;

        const initializeFirebase = () => {
            if (firebaseConfig.apiKey && isMounted) {
                try {
                    // Firebase 앱이 이미 초기화되었는지 확인
                    const app = !getApps().length
                        ? initializeApp(firebaseConfig)
                        : getApp();
                    const auth = getAuth(app);

                    // 실제 Firebase Auth 사용
                    console.log('☁️ Firebase Auth 백그라운드 초기화 완료');

                    const unsubscribe = onAuthStateChanged(
                        auth,
                        (firebaseUser) => {
                            if (!isMounted) return; // 언마운트된 경우 무시

                            if (firebaseUser) {
                                login({
                                    id: firebaseUser.uid,
                                    name: firebaseUser.displayName,
                                    email: firebaseUser.email,
                                    image: firebaseUser.photoURL,
                                });
                            } else {
                                logout();
                            }
                        }
                    );

                    return () => {
                        isMounted = false;
                        unsubscribe();
                    };
                } catch (error) {
                    console.error('Firebase 초기화 실패:', error);
                }
            } else {
                console.error(
                    'Firebase 설정이 올바르지 않습니다. .env.local 파일을 확인해주세요.'
                );
            }
        };

        initializeFirebase();

        return () => {
            isMounted = false;
        };
    }, [login, logout]);

    // Firebase는 백그라운드에서 초기화하고 앱은 즉시 렌더링
    return (
        <>
            {/* 지도가 필요한 페이지에서만 NavermapsProvider 사용 */}
            {children}
        </>
    );
}
