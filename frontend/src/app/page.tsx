import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
    title: '함께 키즈',
    description: '맞벌이 부모를 위한 공동육아 플랫폼',
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="ko">
            {/* tailwind.config.ts에 설정된 Pretendard 폰트가 자동으로 적용됩니다. */}
            <body>{children}</body>
        </html>
    );
}
