'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import MainHeader from '@/components/main/MainHeader';

// ✅ 동적 임포트로 번들 크기 최적화 및 초기 로딩 성능 향상
const MapSection = dynamic(() => import('@/components/main/MapSection'), {
    loading: () => (
        <div className="w-full h-[60vh] bg-gray-100 animate-pulse flex items-center justify-center">
            <div className="text-gray-500">지도를 로딩 중...</div>
        </div>
    ),
    ssr: false, // 지도는 클라이언트에서만 렌더링
});

const ChatSidebar = dynamic(() => import('@/components/chat/ChatSidebar'), {
    loading: () => (
        <div className="fixed right-4 bottom-4 w-80 h-96 bg-white shadow-lg rounded-lg animate-pulse">
            <div className="p-4 space-y-3">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
            </div>
        </div>
    ),
});

export default function DashboardPage() {
    const [isChatbotOpen, setIsChatbotOpen] = useState(false);
    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
    }, []);

    if (!isMounted) {
        return null;
    }

    return (
        <div>
            <main className="relative">
                <MainHeader />
                <MapSection />
                <ChatSidebar
                    isOpen={isChatbotOpen}
                    setIsOpen={setIsChatbotOpen}
                />
            </main>
        </div>
    );
}
