'use client';
import Link from 'next/link';
import Image from 'next/image';
import { useState, useEffect, useRef } from 'react';
import {
    Bell,
    AlertTriangle,
    CalendarClock,
    LogOut,
    User as UserIcon,
} from 'lucide-react';
import { useNotificationStore } from '@/store/notificationStore';
import { useUserStore } from '@/store/userStore';
import { getAuth, signOut } from 'firebase/auth';
import BellIcon from '@/components/ui/BellIcon';

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
    const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
    const modalRef = useRef<HTMLDivElement>(null);
    const userMenuRef = useRef<HTMLDivElement>(null);

    const { notifications, unreadCount, fetchNotifications } =
        useNotificationStore();
    const { user, isLoggedIn } = useUserStore();

    useEffect(() => {
        if (isLoggedIn) {
            fetchNotifications();
        }
    }, [isLoggedIn, fetchNotifications]);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (
                modalRef.current &&
                !modalRef.current.contains(event.target as Node)
            ) {
                setIsModalOpen(false);
            }
            if (
                userMenuRef.current &&
                !userMenuRef.current.contains(event.target as Node)
            ) {
                setIsUserMenuOpen(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () =>
            document.removeEventListener('mousedown', handleClickOutside);
    }, [modalRef, userMenuRef]);

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

    const handleSignOut = async () => {
        const auth = getAuth();
        try {
            await signOut(auth);
            window.location.href = '/';
        } catch (error) {
            console.error('로그아웃 실패:', error);
        }
    };

    return (
        <header className="bg-white shadow-sm sticky top-0 z-50 h-20 flex items-center">
            <div className="container mx-auto px-4 sm:px-6 flex items-center justify-between">
                <div className="flex-1 flex justify-start">
                    <Link href="/" className="flex items-center">
                        <Image
                            src="/images/logo/logowide.png"
                            alt="함께 키즈 로고"
                            width={180}
                            height={60}
                            priority
                        />
                    </Link>
                </div>

                <div className="flex-1 flex items-center justify-end space-x-2 sm:space-x-4">
                    {status === 'authenticated' && user ? (
                        <>
                            <div className="relative" ref={modalRef}>
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
                                    <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg border z-50">
                                        <div className="p-4">
                                            <h4 className="font-semibold text-gray-800">
                                                알림
                                            </h4>
                                            {notifications.length > 0 ? (
                                                <ul className="mt-2 space-y-2">
                                                    {notifications.map(
                                                        (notification) => {
                                                            const {
                                                                icon,
                                                                color,
                                                            } =
                                                                getNotificationStyle(
                                                                    notification.type
                                                                );
                                                            return (
                                                                <li
                                                                    key={
                                                                        notification.id
                                                                    }
                                                                    className={`flex items-center p-2 rounded-md ${color}`}
                                                                >
                                                                    {icon}
                                                                    <span className="ml-2 text-sm text-gray-800">
                                                                        {
                                                                            notification.message
                                                                        }
                                                                    </span>
                                                                </li>
                                                            );
                                                        }
                                                    )}
                                                </ul>
                                            ) : (
                                                <p className="mt-2 text-sm text-gray-500">
                                                    새로운 알림이 없습니다.
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="relative" ref={userMenuRef}>
                                <button
                                    onClick={() =>
                                        setIsUserMenuOpen(!isUserMenuOpen)
                                    }
                                    className="rounded-full overflow-hidden w-9 h-9 border-2 border-gray-200 hover:border-blue-500 transition-colors"
                                >
                                    {user.image ? (
                                        <Image
                                            src={user.image}
                                            alt={user.name || '사용자'}
                                            width={36}
                                            height={36}
                                        />
                                    ) : (
                                        <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                                            <UserIcon className="w-5 h-5 text-gray-500" />
                                        </div>
                                    )}
                                </button>

                                {isUserMenuOpen && (
                                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border z-50">
                                        <div className="px-4 py-3 border-b">
                                            <p className="text-sm font-semibold text-gray-800 truncate">
                                                {user.name}
                                            </p>
                                            <p className="text-xs text-gray-500 truncate">
                                                {user.email}
                                            </p>
                                        </div>
                                        <button
                                            onClick={handleSignOut}
                                            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                                        >
                                            <LogOut className="w-4 h-4 mr-2" />
                                            로그아웃
                                        </button>
                                    </div>
                                )}
                            </div>
                        </>
                    ) : (
                        <Link
                            href="/auth/login"
                            className="bg-blue-600 hover:bg-blue-700 text-white px-4 sm:px-6 py-2 rounded-lg font-medium transition-colors text-sm"
                        >
                            로그인
                        </Link>
                    )}
                </div>
            </div>
        </header>
    );
}
