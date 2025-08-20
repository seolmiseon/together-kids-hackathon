'use client';
import Link from 'next/link';
import Image from 'next/image';
import { Bell, AlertTriangle, CalendarClock, LogOut } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import BellIcon from '@/components/ui/BellIcon';
import { useUserStore } from '@/store/userStore';
import { signOut, useSession } from 'next-auth/react';
import { useNotificationStore } from '@/store/notificationStore';

interface Notification {
    id: number;
    type: 'schedule' | 'emergency' | 'community';
    title: string;
    message: string;
    time: string;
    isRead: boolean;
}

export default function MainHeader() {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const modalRef = useRef<HTMLDivElement>(null);
    const { notifications, unreadCount, fetchNotifications } =
        useNotificationStore();
    const { user, login, logout } = useUserStore();
    const { data: session, status } = useSession();

    useEffect(() => {
        if (status === 'authenticated' && session?.user) {
            // Ensure 'id' is present; fallback to email or a default string if not available
            login({
                id: session.user.email ?? 'unknown-id',
                name: session.user.name ?? null,
                email: session.user.email ?? null,
                image: session.user.image ?? null,
            });
            fetchNotifications();
        } else if (status === 'unauthenticated') {
            logout();
        }
    }, [status, session, login, logout, fetchNotifications]);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (
                modalRef.current &&
                !modalRef.current.contains(event.target as Node)
            ) {
                setIsModalOpen(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () =>
            document.removeEventListener('mousedown', handleClickOutside);
    }, [modalRef]);

    const getNotificationStyle = (type: Notification['type']) => {
        switch (type) {
            case 'emergency':
                return {
                    icon: <AlertTriangle className="w-5 h-5 text-red-500" />,
                    color: 'bg-red-50',
                };
            case 'schedule':
                return {
                    icon: <CalendarClock className="w-5 h-5 text-blue-500" />,
                    color: 'bg-blue-50',
                };
            default:
                return {
                    icon: <Bell className="w-5 h-5 text-gray-500" />,
                    color: 'bg-gray-50',
                };
        }
    };

    return (
        <header className="bg-white shadow-sm sticky top-0 z-50">
            <div className="container mx-auto px-6 py-4 flex items-center justify-between">
                <div className="w-1/3"></div>
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
                <div className="w-1/3 flex items-center justify-end space-x-4">
                    {status === 'authenticated' && user ? (
                        <>
                            <div className="relative" ref={modalRef}>
                                {/* [수정] lucide-react의 Bell 대신 BellIcon 컴포넌트를 사용합니다. */}
                                <button
                                    onClick={() => setIsModalOpen(!isModalOpen)}
                                    className="relative p-2"
                                >
                                    <BellIcon
                                        hasNotification={unreadCount > 0}
                                        count={unreadCount}
                                    />
                                </button>

                                {isModalOpen && (
                                    <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-lg shadow-xl border overflow-hidden animate-fade-in-down">
                                        <div className="p-4 border-b flex justify-between items-center">
                                            <h3 className="font-bold text-gray-800">
                                                알림
                                            </h3>
                                            <span className="text-xs font-bold text-white bg-blue-600 rounded-full px-2 py-1">
                                                {unreadCount}
                                            </span>
                                        </div>
                                        <div className="max-h-96 overflow-y-auto">
                                            {notifications.length > 0 ? (
                                                notifications.map((n) => (
                                                    <div
                                                        key={n.id}
                                                        className={`p-4 flex items-start gap-4 hover:bg-gray-50 transition-colors ${
                                                            !n.isRead
                                                                ? getNotificationStyle(
                                                                      n.type
                                                                  ).color
                                                                : ''
                                                        }`}
                                                    >
                                                        <div className="flex-shrink-0 mt-1">
                                                            {
                                                                getNotificationStyle(
                                                                    n.type
                                                                ).icon
                                                            }
                                                        </div>
                                                        <div className="flex-grow">
                                                            <p
                                                                className={`font-semibold text-sm ${
                                                                    !n.isRead
                                                                        ? 'text-gray-800'
                                                                        : 'text-gray-500'
                                                                }`}
                                                            >
                                                                {n.title}
                                                            </p>
                                                            <p className="text-xs text-gray-500">
                                                                {n.message}
                                                            </p>
                                                            <p className="text-xs text-gray-400 mt-1">
                                                                {n.time}
                                                            </p>
                                                        </div>
                                                        {!n.isRead && (
                                                            <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                                                        )}
                                                    </div>
                                                ))
                                            ) : (
                                                <p className="p-4 text-sm text-gray-500 text-center">
                                                    새로운 알림이 없습니다.
                                                </p>
                                            )}
                                        </div>
                                        <div className="p-2 bg-gray-50 text-center border-t">
                                            <button className="text-sm font-medium text-blue-600 hover:underline">
                                                모든 알림 읽음 처리
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="flex items-center space-x-2">
                                <Image
                                    src={
                                        user.image ||
                                        '/images/default-profile.png'
                                    }
                                    alt={user.name || '사용자'}
                                    width={32}
                                    height={32}
                                    className="rounded-full"
                                />
                                <span className="hidden sm:inline font-medium text-gray-700">
                                    {user.name}
                                </span>
                                <button
                                    onClick={() =>
                                        signOut({ callbackUrl: '/' })
                                    }
                                    className="p-2 hover:bg-gray-100 rounded-full"
                                    title="로그아웃"
                                >
                                    <LogOut className="w-5 h-5 text-gray-500" />
                                </button>
                            </div>
                        </>
                    ) : (
                        <Link
                            href="/auth/login"
                            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                        >
                            로그인
                        </Link>
                    )}
                </div>
            </div>
        </header>
    );
}
