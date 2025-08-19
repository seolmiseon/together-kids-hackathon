import Link from 'next/link';
import Image from 'next/image';
import React from 'react';

export default function Header() {
    return (
        <header className="bg-white shadow-sm sticky top-0 z-50">
            <div className="container mx-auto px-4 py-3 flex items-center justify-between">
                <Link href="/dashboard" className="flex items-center">
                    <Image
                        src="/images/logo/logowide.png"
                        alt="함께 키즈 로고"
                        width={120} // 실제 이미지 크기에 맞게 조절
                        height={40}
                        priority
                    />
                </Link>
                <nav className="hidden md:flex items-center space-x-6 text-gray-600 font-medium">
                    <Link
                        href="/dashboard"
                        className="hover:text-blue-600 transition-colors"
                    >
                        대시보드
                    </Link>
                    <Link
                        href="/chat"
                        className="hover:text-blue-600 transition-colors"
                    >
                        AI 조율
                    </Link>
                    <Link
                        href="/community"
                        className="hover:text-blue-600 transition-colors"
                    >
                        커뮤니티
                    </Link>
                    <Link
                        href="/safety"
                        className="hover:text-blue-600 transition-colors"
                    >
                        안전 관리
                    </Link>
                </nav>
                <div className="flex items-center space-x-4">
                    {/* <NotificationPanel /> */}
                    <div className="w-9 h-9 bg-gray-200 rounded-full cursor-pointer"></div>
                </div>
            </div>
        </header>
    );
}
