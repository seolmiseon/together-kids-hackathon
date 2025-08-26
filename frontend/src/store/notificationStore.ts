import { create } from 'zustand';
import { getAuth } from 'firebase/auth';

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
            const auth = getAuth();
            const user = auth.currentUser;

            if (!user) {
                console.log(
                    'Firebase 사용자가 없어 알림을 가져올 수 없습니다.'
                );
                set({ notifications: [], unreadCount: 0 });
                return;
            }

            const token = await user.getIdToken();

            const apiUrl = process.env.NEXT_PUBLIC_API_URL;
            const response = await fetch(`${apiUrl}/alerts/`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
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

    markAsRead: async (id: number) => {
        const updatedNotifications = get().notifications.map((n) =>
            n.id === id ? { ...n, isRead: true } : n
        );
        set({
            notifications: updatedNotifications,
            unreadCount: updatedNotifications.filter((n) => !n.isRead).length,
        });

        try {
            const auth = getAuth();
            const user = auth.currentUser;
            if (!user) return;

            const token = await user.getIdToken();
            const apiUrl = process.env.NEXT_PUBLIC_API_URL;

            await fetch(`${apiUrl}/alerts/${id}/read/`, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
        } catch (error) {
            console.error('알림 읽음 처리 실패:', error);
            // (선택) 읽음 처리 실패 시, UI를 원래대로 되돌리는 로직을 추가할 수 있습니다.
        }
    },
}));
