import type { Metadata } from 'next';
import './globals.css';
import SessionProviderWrapper from './providers/SessionProviderWrapper';
import Script from 'next/script';

export const metadata: Metadata = {
    title: '함께 키즈',
    description: '맞벌이 부모를 위한 공동육아 플랫폼',
    icons: {
        icon: '/favicon.svg',
    },
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    const KAKAO_MAP_KEY = process.env.NEXT_PUBLIC_KAKAO_MAP_KEY;

    return (
        <html lang="ko">
            <head>
                <Script
                    src={`//dapi.kakao.com/v2/maps/sdk.js?appkey=${KAKAO_MAP_KEY}`}
                    strategy="beforeInteractive"
                />
            </head>
            <body>
                <SessionProviderWrapper>{children}</SessionProviderWrapper>
            </body>
        </html>
    );
}
