import { create } from 'zustand';

// --- 타입 정의 ---
interface User {
    id: string;
    name: string | null;
    email: string | null;
    image: string | null; // 프로필 이미지 URL
}

interface UserState {
    user: User | null;
    isLoggedIn: boolean;
    login: (userData: User) => void;
    logout: () => void;
    updateUser: (updatedData: Partial<User>) => void;
}

export const useUserStore = create<UserState>((set) => ({
    user: null,
    isLoggedIn: false,

    login: (userData) => {
        set({
            user: userData,
            isLoggedIn: true,
        });
    },

    logout: () => {
        set({
            user: null,
            isLoggedIn: false,
        });
    },
    updateUser: (updatedData) => {
        set((state) => {
            if (!state.user) return {};
            return {
                user: {
                    ...state.user,
                    ...updatedData,
                },
            };
        });
    },
}));
