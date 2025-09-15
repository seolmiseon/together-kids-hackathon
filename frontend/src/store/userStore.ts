import { create } from 'zustand';
import { getAuth } from 'firebase/auth';

// --- 타입 정의 ---
interface User {
    id: string;
    name: string | null;
    email: string | null;
    image: string | null;
}

interface UserState {
    user: User | null;
    isLoggedIn: boolean;
    isLoading: boolean;
    login: (userData: User) => void;
    logout: () => void;
    updateUser: (updatedData: Partial<User>) => void;
    // 🚀 통합 소셜 로그인 처리
    handleSocialLoginComplete: (router: any) => Promise<void>;
    // 🚀 프로필 설정 완료 후 처리
    handleProfileSetupComplete: (router: any) => Promise<void>;
}

export const useUserStore = create<UserState>((set, get) => ({
    user: null,
    isLoggedIn: false,
    isLoading: false,

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

    // 🚀 모든 소셜 로그인 후 공통 처리 로직
    handleSocialLoginComplete: async (router) => {
        set({ isLoading: true });
        
        try {
            const auth = getAuth();
            const user = auth.currentUser;
            
            if (!user) {
                console.log('❌ 사용자 정보 없음 → 로그인으로 이동');
                router.replace('/auth/login');
                return;
            }

            const token = await user.getIdToken();
            const apiUrl = process.env.NEXT_PUBLIC_API_URL;

            // 1. 사용자 프로필 상태 확인
            const profileResponse = await fetch(`${apiUrl}/users/profile`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (profileResponse.ok) {
                const profileData = await profileResponse.json();

                // 2. 프로필이 완성되어 있는지 확인
                if (profileData.full_name && profileData.apartment_complex) {
                    // 3. 자녀 정보도 확인
                    const childrenResponse = await fetch(`${apiUrl}/children/`, {
                        headers: {
                            Authorization: `Bearer ${token}`,
                            'Content-Type': 'application/json',
                        },
                    });

                    if (childrenResponse.ok) {
                        const childrenData = await childrenResponse.json();

                        if (childrenData.children && childrenData.children.length > 0) {
                            // ✅ 완전한 프로필 → 대시보드로
                            console.log('✅ 완전한 프로필 확인 → 대시보드로 이동');
                            router.replace('/dashboard');
                        } else {
                            // ⚠️ 자녀 정보 없음 → 프로필 설정으로
                            console.log('⚠️ 자녀 정보 없음 → 프로필 설정으로 이동');
                            router.replace('/auth/profile');
                        }
                    } else {
                        console.log('⚠️ 자녀 정보 조회 실패 → 프로필 설정으로 이동');
                        router.replace('/auth/profile');
                    }
                } else {
                    console.log('⚠️ 기본 프로필 정보 없음 → 프로필 설정으로 이동');
                    router.replace('/auth/profile');
                }
            } else {
                console.log('⚠️ 프로필 조회 실패 → 프로필 설정으로 이동');
                router.replace('/auth/profile');
            }
        } catch (error) {
            console.error('소셜 로그인 후 처리 중 오류:', error);
            router.replace('/auth/login');
        } finally {
            set({ isLoading: false });
        }
    },

    // 🚀 프로필 설정 완료 후 처리 (항상 대시보드로)
    handleProfileSetupComplete: async (router) => {
        console.log('✅ 프로필 설정 완료 → 대시보드로 이동');
        router.replace('/dashboard');
    },
}));
