import { create } from 'zustand';

// --- 타입 정의 ---
// 백엔드 API 응답과 일치해야 합니다.
interface Notification {
    id: number;
    type: 'schedule' | 'emergency' | 'community';
    title: string;
    message: string;
    time: string;
    isRead: boolean;
}

interface NotificationState {
    notifications: Notification[];
    unreadCount: number;
    fetchNotifications: () => Promise<void>;
    markAsRead: (id: number) => void;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
    notifications: [],
    unreadCount: 0,

    fetchNotifications: async () => {
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL;
            // (주의: 실제 구현 시에는 로그인 인증 토큰을 헤더에 포함해야 합니다.)
            const response = await fetch(`${apiUrl}/alerts`);

            if (!response.ok) {
                throw new Error('알림 데이터를 가져오는 데 실패했습니다.');
            }

            const responseData = await response.json();
            const data: Notification[] = responseData.alerts;

            set({
                notifications: data,
                unreadCount: data.filter((n) => !n.isRead).length,
            });
        } catch (error) {
            console.error('알림 로딩 실패:', error);
            // 에러 발생 시 빈 배열로 설정
            set({ notifications: [], unreadCount: 0 });
        }
    },

    // 특정 알림을 읽음 처리하는 함수
    markAsRead: (id: number) => {
        const updatedNotifications = get().notifications.map((n) =>
            n.id === id ? { ...n, isRead: true } : n
        );
        set({
            notifications: updatedNotifications,
            unreadCount: updatedNotifications.filter((n) => !n.isRead).length,
        });

        fetch(`/api/notifications/${id}/read`, { method: 'POST' });
    },
}));
