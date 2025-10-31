import { getAuth, signOut } from 'firebase/auth';

/**
 * 세션 관리 유틸리티
 * - 24시간 후 자동 로그아웃
 * - 마지막 활동 시간 추적
 */

const SESSION_TIMEOUT = 24 * 60 * 60 * 1000; // 24시간 (밀리초)
const LAST_ACTIVITY_KEY = 'lastActivityTime';
const AUTO_LOGOUT_TIMER_KEY = 'autoLogoutTimer';

export class SessionManager {
    private checkInterval: NodeJS.Timeout | null = null;

    /**
     * 세션 타이머 시작
     */
    startSessionTimer() {
        // 기존 타이머 정리
        this.clearSessionTimer();

        // 현재 시간 저장
        this.updateLastActivity();

        // 24시간 후 자동 로그아웃 타이머 설정
        const timerId = setTimeout(() => {
            this.handleAutoLogout();
        }, SESSION_TIMEOUT);

        // 타이머 ID 저장 (디버깅용)
        if (typeof window !== 'undefined') {
            (window as any)[AUTO_LOGOUT_TIMER_KEY] = timerId;
        }

        // 5분마다 세션 유효성 검사
        this.checkInterval = setInterval(() => {
            this.checkSessionValidity();
        }, 5 * 60 * 1000);

        console.log('✅ 세션 타이머 시작 - 24시간 후 자동 로그아웃');
    }

    /**
     * 마지막 활동 시간 업데이트
     */
    updateLastActivity() {
        if (typeof window !== 'undefined') {
            localStorage.setItem(LAST_ACTIVITY_KEY, Date.now().toString());
        }
    }

    /**
     * 세션 유효성 검사
     */
    checkSessionValidity() {
        if (typeof window === 'undefined') return;

        const lastActivity = localStorage.getItem(LAST_ACTIVITY_KEY);
        if (!lastActivity) return;

        const lastActivityTime = parseInt(lastActivity, 10);
        const currentTime = Date.now();
        const timeDiff = currentTime - lastActivityTime;

        console.log(`🕐 세션 체크: ${Math.floor(timeDiff / 1000 / 60)}분 경과`);

        // 24시간 경과 시 로그아웃
        if (timeDiff >= SESSION_TIMEOUT) {
            console.log('⏰ 세션 만료 - 자동 로그아웃 실행');
            this.handleAutoLogout();
        }
    }

    /**
     * 자동 로그아웃 처리
     */
    async handleAutoLogout() {
        try {
            const auth = getAuth();
            await signOut(auth);
            
            // 세션 정보 정리
            this.clearSessionTimer();
            if (typeof window !== 'undefined') {
                localStorage.removeItem(LAST_ACTIVITY_KEY);
                alert('보안을 위해 24시간이 경과하여 자동 로그아웃되었습니다.');
                window.location.href = '/auth/login';
            }

            console.log('✅ 자동 로그아웃 완료');
        } catch (error) {
            console.error('❌ 자동 로그아웃 실패:', error);
        }
    }

    /**
     * 세션 타이머 정리
     */
    clearSessionTimer() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }

        if (typeof window !== 'undefined') {
            const timerId = (window as any)[AUTO_LOGOUT_TIMER_KEY];
            if (timerId) {
                clearTimeout(timerId);
                delete (window as any)[AUTO_LOGOUT_TIMER_KEY];
            }
        }

        console.log('🧹 세션 타이머 정리 완료');
    }

    /**
     * 수동 로그아웃 (즉시 실행)
     */
    async logout() {
        try {
            const auth = getAuth();
            await signOut(auth);
            
            this.clearSessionTimer();
            if (typeof window !== 'undefined') {
                localStorage.removeItem(LAST_ACTIVITY_KEY);
            }

            console.log('✅ 수동 로그아웃 완료');
        } catch (error) {
            console.error('❌ 로그아웃 실패:', error);
            throw error;
        }
    }
}

// 싱글톤 인스턴스
export const sessionManager = new SessionManager();
