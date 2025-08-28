'use client';

import { useEffect } from 'react';
import { initializeApp, getApps } from 'firebase/app';
import { getAuth, onAuthStateChanged } from 'firebase/auth';
import { useUserStore } from '@/store/userStore';
import { NavermapsProvider } from 'react-naver-maps';
import React from 'react';

const firebaseConfig = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
    measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID,
};

if (!getApps().length) {
    initializeApp(firebaseConfig);
}

export default function Providers({ children }: { children: React.ReactNode }) {
    const { login, logout } = useUserStore();

    useEffect(() => {
        const auth = getAuth();
        const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
            if (firebaseUser) {
                // Firebase에 로그인되면, Zustand 스토어의 상태도 로그인으로 변경합니다.
                login({
                    id: firebaseUser.uid,
                    name: firebaseUser.displayName,
                    email: firebaseUser.email,
                    image: firebaseUser.photoURL,
                });
            } else {
                logout();
            }
        });

        return () => unsubscribe();
    }, [login, logout]);

    return (
        <NavermapsProvider
            ncpClientId={process.env.NEXT_PUBLIC_NAVER_MAP_CLIENT_ID || ''}
        >
            {children}
        </NavermapsProvider>
    );
}
