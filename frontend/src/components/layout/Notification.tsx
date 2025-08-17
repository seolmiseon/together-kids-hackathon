import BellIcon from '@/components/ui/BellIcon';
import { useState } from 'react';

interface Notification {
    id: number;
    type: 'schedule' | 'safety' | 'community';
    title: string;
    message: string;
    time: string;
    isRead: boolean;
}

type NotificationColorType = 'schedule' | 'safety' | 'community';

export default function NotificationPanel() {
    const [isOpen, setIsOpen] = useState(false);
    const [notifications, setNotifications] = useState<Notification[]>([
        {
            id: 1,
            type: 'schedule',
            title: '변우석엄마가 내일 하원 도움을 요청했어요',
            message: '김지연이와 함께 3시에 하원 가능하신가요?',
            time: '10분 전',
            isRead: false,
        },
        {
            id: 2,
            type: 'safety',
            title: '안전 알림: 정상 도착 완료',
            message: '김지연이가 어린이집에 안전하게 도착했어요',
            time: '30분 전',
            isRead: true,
        },
        {
            id: 3,
            type: 'community',
            title: '새로운 모임 개설',
            message: '101동 주말 놀이 모임에 참여해보세요!',
            time: '1시간 전',
            isRead: false,
        },
    ]);

    const unreadCount = notifications.filter((n) => !n.isRead).length;

    const getNotificationIcon = (type: NotificationColorType) => {
        switch (type) {
            case 'schedule':
                return '📅';
            case 'safety':
                return '🛡️';
            case 'community':
                return '👥';
            default:
                return '📢';
        }
    };

    const getNotificationColor = (type: NotificationColorType) => {
        switch (type) {
            case 'schedule':
                return 'border-l-blue-500 bg-blue-50';
            case 'safety':
                return 'border-l-green-500 bg-green-50';
            case 'community':
                return 'border-l-purple-500 bg-purple-50';
            default:
                return 'border-l-gray-500 bg-gray-50';
        }
    };

    const handleNotificationClick = (notificationId: number): void => {
        setNotifications((prev) =>
            prev.map((n) =>
                n.id === notificationId ? { ...n, isRead: true } : n
            )
        );
    };

    const markAllAsRead = (): void => {
        setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
    };

    return (
        <div className="relative">
            {/* 알림 버튼 */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="relative p-2 hover:bg-gray-100 rounded-full transition-colors"
                aria-label="알림 패널 열기"
            >
                <BellIcon
                    hasNotification={unreadCount > 0}
                    count={unreadCount}
                />
            </button>

            {/* 알림 패널 */}
            {isOpen && (
                <>
                    {/* 배경 오버레이 */}
                    <div
                        className="fixed inset-0 z-40"
                        aria-label="알림 패널 닫기"
                        onClick={() => setIsOpen(false)}
                    />

                    {/* 알림 드롭다운 */}
                    <div className="absolute right-0 top-full mt-2 w-96 bg-white rounded-lg shadow-lg border z-50 max-h-96 overflow-hidden">
                        {/* 헤더 */}
                        <div className="p-4 border-b bg-gray-50">
                            <div className="flex items-center justify-between">
                                <h3 className="font-semibold text-gray-800">
                                    알림
                                </h3>
                                <span className="text-xs text-gray-500">
                                    {unreadCount > 0 &&
                                        `${unreadCount}개의 새 알림`}
                                </span>
                            </div>
                        </div>

                        {/* 알림 목록 */}
                        <div className="max-h-80 overflow-y-auto">
                            {notifications.length > 0 ? (
                                notifications.map((notification) => (
                                    <div
                                        key={notification.id}
                                        className={`p-4 border-b border-l-4 hover:bg-gray-50 cursor-pointer transition-colors ${getNotificationColor(
                                            notification.type
                                        )} ${
                                            !notification.isRead
                                                ? 'bg-opacity-100'
                                                : 'bg-opacity-30'
                                        }`}
                                        onClick={() => {
                                            handleNotificationClick(
                                                notification.id
                                            );
                                        }}
                                    >
                                        <div className="flex items-start space-x-3">
                                            <div className="text-xl">
                                                {getNotificationIcon(
                                                    notification.type
                                                )}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p
                                                    className={`text-sm ${
                                                        !notification.isRead
                                                            ? 'font-semibold text-gray-800'
                                                            : 'text-gray-700'
                                                    }`}
                                                >
                                                    {notification.title}
                                                </p>
                                                <p className="text-xs text-gray-600 mt-1">
                                                    {notification.message}
                                                </p>
                                                <p className="text-xs text-gray-500 mt-2">
                                                    {notification.time}
                                                </p>
                                            </div>
                                            {!notification.isRead && (
                                                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                                            )}
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="p-8 text-center text-gray-500">
                                    <div className="text-4xl mb-2">🔔</div>
                                    <p>새로운 알림이 없어요</p>
                                </div>
                            )}
                        </div>

                        {/* 푸터 */}
                        {notifications.length > 0 && (
                            <div className="p-3 bg-gray-50 border-t">
                                <button
                                    className="w-full text-sm text-blue-600 hover:text-blue-800 font-medium"
                                    onClick={markAllAsRead}
                                >
                                    모든 알림 읽음으로 표시
                                </button>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}
