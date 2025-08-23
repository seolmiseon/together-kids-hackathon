'use client';
import { SessionProvider } from 'next-auth/react';
import { NavermapsProvider } from 'react-naver-maps';
import React from 'react';

interface Props {
    children: React.ReactNode;
}

export default function SessionProviderWrapper({ children }: Props) {
    return (
        <SessionProvider>
            <NavermapsProvider
                ncpClientId={process.env.NEXT_PUBLIC_NAVER_MAP_CLIENT_ID || ''}
            >
                {children}
            </NavermapsProvider>
        </SessionProvider>
    );
}
