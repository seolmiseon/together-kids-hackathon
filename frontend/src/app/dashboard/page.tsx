'use client';

import { useState } from 'react';
import MapSection from '@/components/main/MapSection';
import ChatbotSlidebar from '@/components/main/ChatbotSlidebar';
import MainHeader from '@/components/main/MainHeader';

export default function DashboardPage() {
    const [isChatbotOpen, setIsChatbotOpen] = useState(false);

    return (
        <div>
            <MainHeader />

            <main className="relative">
                {/* 지도 섹션 - 메인 화면 */}
                <MapSection />

                {/* 챗봇 사이드바 */}
                <ChatbotSlidebar
                    isOpen={isChatbotOpen}
                    setIsOpen={setIsChatbotOpen}
                />
            </main>
        </div>
    );
}
