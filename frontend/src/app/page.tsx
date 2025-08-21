'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import MainHeader from '@/components/main/MainHeader';
import MapSection from '@/components/main/MapSection';

export default function LandingPage() {
    const router = useRouter();
    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
    }, []);

    if (!isMounted) {
        return null;
    }

    return (
        <div className="relative min-h-screen w-full overflow-hidden">
            <div className="absolute inset-0 z-0">
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

            {/* 4. 챗봇 열기 버튼은 그대로 유지하되, 클릭 시 로그인 페이지로 이동합니다. */}
            <button
                onClick={() => router.push('/auth/login')}
                className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg transition-colors z-40 animate-bounce"
                aria-label="AI 도우미와 대화하려면 로그인하세요"
                title="AI 도우미와 대화하려면 로그인하세요"
            >
                <Image
                    src="/images/logo/logosymbol.png"
                    alt="함께키즈 AI"
                    width={32}
                    height={32}
                    className="w-8 h-8"
                />
            </button>
        </div>
    );
}
