'use client';

import { useEffect, useState } from 'react';
import MapSection from '@/components/main/MapSection';
import ChatSidebar from '@/components/chat/ChatSidebar';
import MainHeader from '@/components/main/MainHeader';

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
