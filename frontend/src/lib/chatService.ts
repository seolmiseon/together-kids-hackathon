// 채팅 서비스 API 호출 함수들
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hackathon-integrated-service-529342898795.asia-northeast3.run.app'; // 배포 서버 사용

export interface ChatMessage {
    id: string;
    message: string;
    timestamp: string;
    type: 'user' | 'ai';
    userId?: string;
}

export interface ChatResponse {
    response: string;
    emotion?: string;
    intent?: string;
    timestamp: string;
}

// AI 채팅 메시지 전송
export const sendChatMessage = async (
    message: string,
    userId?: string
): Promise<ChatResponse> => {
    try {
        const response = await axios.post(`${API_BASE_URL}/chat`, {
            message,
            user_id: userId,
        });
        return response.data;
    } catch (error) {
        console.error('채팅 메시지 전송 실패:', error);
        throw new Error('채팅 서비스에 연결할 수 없습니다.');
    }
};

// 채팅 기록 조회
export const getChatHistory = async (userId: string): Promise<ChatMessage[]> => {
    try {
        const response = await axios.get(`${API_BASE_URL}/chat/history`, {
            params: { user_id: userId },
        });
        return response.data.messages || [];
    } catch (error) {
        console.error('채팅 기록 조회 실패:', error);
        return [];
    }
};

// 감정 분석
export const analyzeEmotion = async (text: string): Promise<any> => {
    try {
        const response = await axios.post(`${API_BASE_URL}/chat/emotion-analysis`, {
            text,
        });
        return response.data;
    } catch (error) {
        console.error('감정 분석 실패:', error);
        throw error;
    }
};

// AI 응답 처리
export const processAiResponse = (aiData: ChatResponse): string => {
    // AI 응답 후처리 로직 (필요시 확장 가능)
    return aiData.response || '응답을 처리할 수 없습니다.';
};

// 지도 표시 처리 - 실제 지도 컴포넌트와 연동
export const handleMapDisplay = (places: any[]) => {
    console.log('🗺️ 지도에 장소 표시 요청:', places);
    
    // 장소 데이터 정제 - AI 응답에서 실제 장소명만 추출
    const cleanedPlaces = places.map(place => {
        let cleanName = place.name || '';
        
        console.log(`🔍 원본 장소명: "${cleanName}"`);
        
        // 패턴 1: "OO 놀이공원 에서는..." → "OO 놀이공원"
        if (cleanName.includes(' 에서는') || cleanName.includes(' 에서')) {
            cleanName = cleanName.split(/ 에서[는]?/)[0];
        }
        
        // 패턴 2: "키즈카페는 다양한..." → "키즈카페"  
        if (cleanName.includes('는 ') || cleanName.includes('은 ')) {
            cleanName = cleanName.split(/[는은] /)[0];
        }
        
        // 패턴 3: "OO공원이 좋은..." → "OO공원"
        if (cleanName.includes('이 ') || cleanName.includes('가 ')) {
            cleanName = cleanName.split(/[이가] /)[0];
        }
        
        // 패턴 4: "놀이공원에..." → "놀이공원"
        if (cleanName.includes('에 ') || cleanName.includes('에서')) {
            cleanName = cleanName.split(/에[서]? /)[0];
        }
        
        // 패턴 5: 문장 끝 조사 제거 ("공원을", "카페도" → "공원", "카페")
        cleanName = cleanName.replace(/[을를도와과]$/, '');
        
        // 패턴 6: 첫 번째 의미있는 단어 조합 추출 (2단어까지)
        const words = cleanName.split(' ').filter((word: string) => word.length >= 1);
        if (words.length >= 2) {
            // "OO 놀이공원", "키즈 카페" 같은 경우 2단어 유지
            const possibleName = words.slice(0, 2).join(' ');
            if (possibleName.length <= 10) { // 너무 길지 않은 경우만
                cleanName = possibleName;
            } else {
                cleanName = words[0]; // 첫 단어만
            }
        } else if (words.length === 1) {
            cleanName = words[0];
        }
        
        // 특수문자 제거 (한글, 영문, 숫자, 공백만 유지)
        cleanName = cleanName.replace(/[^가-힣a-zA-Z0-9\s]/g, '').trim();
        
        // 최종 검증: 너무 긴 경우 첫 단어만 사용
        if (cleanName.length > 15) {
            cleanName = cleanName.split(' ')[0];
        }
        
        console.log(`✅ 정제된 장소명: "${cleanName}"`);
        
        return {
            ...place,
            name: cleanName || place.name, // 정제 실패 시 원본 사용
            originalName: place.name, // 원본 이름 보존
        };
    });
    
    // MapSection 컴포넌트의 전역 함수 호출
    if (typeof window !== 'undefined' && (window as any).displaySearchResults) {
        console.log('✅ 지도 함수 호출 성공');
        (window as any).displaySearchResults(cleanedPlaces);
    } else {
        console.warn('⚠️ 지도 함수를 찾을 수 없습니다. 지도 컴포넌트가 로드되지 않았을 수 있습니다.');
        
        // 3초 후 재시도
        setTimeout(() => {
            if (typeof window !== 'undefined' && (window as any).displaySearchResults) {
                console.log('🔄 지도 함수 재시도 성공');
                (window as any).displaySearchResults(cleanedPlaces);
            } else {
                console.error('❌ 지도 연동 실패: displaySearchResults 함수 없음');
            }
        }, 3000);
    }
};

// 에러 메시지 생성 (Message 타입에 맞게)
export const createErrorMessage = (error: Error) => {
    return {
        id: Date.now(),
        content: '죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해 주세요.',
        timestamp: new Date(),
        type: 'ai' as const,
    };
};

export default {
    sendMessage: sendChatMessage,
    getHistory: getChatHistory,
    analyzeEmotion,
    processAiResponse,
    handleMapDisplay,
    createErrorMessage,
};