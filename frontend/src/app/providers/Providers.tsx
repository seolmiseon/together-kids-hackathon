'use client';

import { useEffect } from 'react';
import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, onAuthStateChanged, signOut } from 'firebase/auth';
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
        console.log('🔍 Firebase Config 체크:', firebaseConfig.apiKey ? '✅' : '❌');
        let isMounted = true;

        const initializeFirebase = () => {
            if (firebaseConfig.apiKey && isMounted) {
                try {
                    const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
                    const auth = getAuth(app);

                    console.log('☁️ Firebase Auth 백그라운드 초기화 완료');

                    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
                        if (!isMounted) return;

                        if (firebaseUser) {
                            // 🚀 Zustand에 사용자 정보 저장
                            login({
                                id: firebaseUser.uid,
                                name: firebaseUser.displayName,
                                email: firebaseUser.email,
                                image: firebaseUser.photoURL,
                            });
                            console.log('✅ Zustand 로그인 상태 동기화 완료');
                        } else {
                            // 🚀 Zustand 로그아웃 상태 동기화
                            logout();
                            console.log('🚪 Zustand 로그아웃 상태 동기화 완료');
                        }
                    });

                    return () => {
                        isMounted = false;
                        unsubscribe();
                    };
                } catch (error) {
                    console.error('Firebase 초기화 실패:', error);
                }
            } else {
                console.error('Firebase 설정이 올바르지 않습니다. .env.local 파일을 확인해주세요.');
            }
        };

        initializeFirebase();

        return () => {
            isMounted = false;
        };
    }, [login, logout]);

    return <>{children}</>;
}
