'use client';
import Link from 'next/link';
import Image from 'next/image';
import { useState } from 'react';
import BellIcon from '@/components/ui/BellIcon';

export default function MainHeader() {
    const [notifications] = useState([
        {
            id: 1,
            type: 'schedule',
            title: '변우석엄마가 내일 하원 도움을 요청했어요',
            message: '김지연이와 함께 3시에 하원 가능하신가요?',
            time: '10분 전',
            isRead: false,
        },
    ]);

    const unreadCount = notifications.filter((n) => !n.isRead).length;

    return (
        <header className="bg-white shadow-sm sticky top-0 z-50">
            <div className="container mx-auto px-6 py-4 flex items-center justify-between">
                {/* 좌측: 빈 공간 (균형을 위해) */}
                <div className="w-1/3"></div>

                {/* 중앙: 로고 */}
                <div className="w-1/3 flex justify-center">
                    <Link href="/" className="flex items-center">
                        <Image
                            src="/images/logo/logowide.png"
                            alt="함께 키즈 로고"
                            width={160}
                            height={50}
                            priority
                        />
                    </Link>
                </div>

                {/* 우측: 로그인 버튼과 알림 아이콘 */}
                <div className="w-1/3 flex items-center justify-end space-x-4">
                    {/* 알림 아이콘 */}
                    <button className="relative p-2 hover:bg-gray-100 rounded-full transition-colors">
                        <BellIcon
                            hasNotification={unreadCount > 0}
                            count={unreadCount}
                        />
                    </button>

                    {/* 로그인 버튼 */}
                    <Link
                        href="/login"
                        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                    >
                        로그인
                    </Link>
                </div>
            </div>
        </header>
    );
}
