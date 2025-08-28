import type { Metadata } from 'next';
import './globals.css';
import Providers from './providers/Providers';

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
    return (
        <html lang="ko">
            <body>
                <Providers>{children}</Providers>
            </body>
        </html>
    );
}
