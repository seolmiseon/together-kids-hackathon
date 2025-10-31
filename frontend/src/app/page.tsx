'use client';

import { useRouter } from 'next/navigation';
import Image from 'next/image';
import dynamic from 'next/dynamic';
import { useState } from 'react';
import MainHeader from '@/components/main/MainHeader';

// ✅ 지도 컴포넌트 동적 로딩으로 초기 번들 크기 최적화
const MapSection = dynamic(() => import('@/components/main/MapSection'), {
    loading: () => (
        <div className="w-full h-full bg-gradient-to-br from-blue-50 to-indigo-100 animate-pulse flex items-center justify-center">
            <div className="text-blue-500 text-sm">
                실시간 지도를 불러오는 중...
            </div>
        </div>
    ),
    ssr: false, // 지도 API는 클라이언트에서만 실행
});

// ✅ 챗봇 컴포넌트 동적 로딩
const ChatSidebar = dynamic(() => import('@/components/chat/ChatSidebar'), {
    loading: () => null,
    ssr: false,
});

export default function LandingPage() {
    const router = useRouter();
    const [isChatOpen, setIsChatOpen] = useState(false); // 테스트용 챗봇 상태

    return (
        <div className="relative min-h-screen w-full overflow-hidden">
            <div className="absolute inset-0 z-0 pt-24">
                <MapSection />
            </div>

            <div className="relative z-10 flex flex-col min-h-screen">
                <MainHeader />

                {/* 메인 콘텐츠 영역 */}
                <main className="flex-grow flex items-center">
                    <div className="container mx-auto px-6">
                        <div className="w-full md:w-1/2 lg:w-2/5">
                            <div className="bg-white/80 backdrop-blur-sm p-8 rounded-lg shadow-lg">
                                <h1 className="text-4xl md:text-5xl font-bold text-gray-800 leading-tight mb-4">
                                    AI와 함께, 이웃과 함께
                                    <br />
                                    우리 아이 등하원을 스마트하게
                                </h1>
                                <p className="text-lg text-gray-600 mb-8">
                                    '함께 키즈'는 AI 기반 일정 조율과 실시간
                                    위치 공유로 맞벌이 부모의 등하원 고민을
                                    해결합니다.
                                </p>
                                <button
                                    onClick={() => router.push('/auth/login')}
                                    className="px-8 py-4 bg-blue-600 text-white font-bold text-lg rounded-lg hover:bg-blue-700 transition-transform hover:scale-105"
                                >
                                    지금 바로 시작하기
                                </button>
                            </div>
                        </div>
                    </div>
                </main>
            </div>

            {/* 테스트용 챗봇 컴포넌트 */}
            <ChatSidebar isOpen={isChatOpen} setIsOpen={setIsChatOpen} />
        </div>
    );
}
